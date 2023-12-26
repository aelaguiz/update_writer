import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Pinecone
from tenacity import retry, stop_after_attempt, wait_fixed



import pinecone
from . import lib_logging

docdb = None
llm = None
pinecone_index = None

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
EMAILDB_PATH = None
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE"))

COMPANY_ENV = None

def set_company_environment(company_env):
    global COMPANY_ENV
    global EMAILDB_PATH

    EMAILDB_PATH = os.getenv(f'{company_env}_EMAILDB_PATH')
    COMPANY_ENV = company_env

def get_embedding_fn():
    return OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'), timeout=30)

def get_llm():
    global llm 

    if not llm:
        llm = ChatOpenAI(model_name=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE)

    return llm

def get_docdb():
    global docdb
    global pinecone_index

    if not docdb:
        # initialize pinecone
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=os.getenv("PINECONE_ENV"),  # next to api key in console
        )

        pinecone_index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))
        docdb = Pinecone(pinecone_index, get_embedding_fn(), "text")


    return docdb

def get_slack_ids():
    # filter": {"type": {"$eq": "website"}}})

    # global pinecone_index

    # max_vectors = 1000  # Replace with the actual or estimated number of vectors
    # vector_ids = [i["id"] for i in pinecone_index.fetch_metadata(page_size=max_vectors)["results"]]

    # # Fetching all documents using the IDs
    # documents = [pinecone_index.fetch(id=v_id) for v_id in vector_ids]
    # print(documents)


    return []

    # res = docdb.get(include=['metadatas'], )
    # for id, metadata in zip(res['ids'], res['metadatas']):
    #     if metadata.get('type') == 'slack':
    #         print(id, metadata)
    #         yield metadata['slack_id']

def get_email_ids():
    # filter": {"type": {"$eq": "website"}}})

    docdb = get_docdb()
    res = docdb.get(include=['metadatas'])
    for id, metadata in zip(res['ids'], res['metadatas']):
        if metadata.get('type') == 'email':
            print(id, metadata)
            yield metadata['email_id']

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))  # Retries up to 3 times with a 2-second wait between retries
def add_texts_with_retry(docdb, texts, metadatas):
    docdb.add_texts(texts, metadatas=metadatas)


def add_email(email_details):
    docdb = get_docdb()

    logger = lib_logging.get_logger()
    try:
        timestamp = int(email_details['send_date'].timestamp())

        metadata = {
            'type': 'email',
            'email_id': email_details['id'],
            'thread_id': email_details['threadId'],
            'from_address': email_details['from'],
            'send_date': timestamp,
            'to_address': email_details['to'] if email_details['to'] else '',
            'subject': email_details['subject'] if email_details['subject'] else '',
        }
        # logger.info(f"Metadata: {metadata}")
        add_texts_with_retry(docdb, [email_details['original_message']], [metadata])
    except Exception as e:
        logger.error(f"Error loading document into db: {e}")
        raise RuntimeError(f"Error loading document into db: {e}")

def add_emails(email_details):
    docdb = get_docdb()

    logger = lib_logging.get_logger()
    try:
        texts = []
        mds = []
        for email in email_details:
            try:
                # print(email)
                timestamp = int(email['send_date'].timestamp())

                metadata = {
                    'type': 'email',
                    'email_id': email['id'],
                    'thread_id': email['threadId'],
                    'from_address': email['from'],
                    'send_date': timestamp,
                    'to_address': email['to'] if email['to'] else '',
                    'subject': email['subject'] if email['subject'] else '',
                }

                texts.append(email['original_message'])
                mds.append(metadata)
            except Exception as e:
                logger.error(f"Error setting metadata: {e}")
                raise RuntimeError(f"Error setting metadata: {e}")

        # logger.info(f"Metadata: {metadata}")
        # logger.info(f"Adding {len(texts)} emails to db")
        # logger.debug(len(texts))
        # logger.debug(mds)
        add_texts_with_retry(docdb, texts, mds)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error loading document into db: {e}")
        raise RuntimeError(f"Error loading document into db: {e}")

def add_docs(docs):
    logger = lib_logging.get_logger()
    docdb = get_docdb()

    try:
        add_texts_with_retry(docdb, [d.page_content for d in docs], [d.metadata for d in docs])
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error loading document into db: {e}")
        raise RuntimeError(f"Error loading document into db: {e}")