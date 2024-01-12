import os
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Pinecone
from tenacity import retry, stop_after_attempt, wait_fixed
from langchain.indexes import SQLRecordManager, index
from langchain.cache import SQLiteCache
from langchain.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from langchain.globals import set_llm_cache
import httpx



import pinecone
from . import lib_logging

docdb = None
llm = None
pinecone_index = None
_record_manager = None
_json_llm = None

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
EMAILDB_PATH = None
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE"))

COMPANY_ENV = None

def set_company_environment(company_env):
    global COMPANY_ENV
    global EMAILDB_PATH

    EMAILDB_PATH = os.getenv(f'{company_env}_EMAILDB_PATH')
    COMPANY_ENV = company_env


    set_llm_cache(SQLiteCache(database_path=f".{company_env}_langchain.db"))


    
def get_company_environment():
    global COMPANY_ENV
    return COMPANY_ENV

def get_embedding_fn():
    return OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'), timeout=30)

def get_llm():
    global llm 

    if not llm:
        llm = ChatOpenAI(model_name=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE)

    return llm

def get_json_llm():
    global _json_llm 

    if not _json_llm:
        _json_llm = ChatOpenAI(model_name=OPENAI_MODEL, temperature=OPENAI_TEMPERATURE, timeout=httpx.Timeout(15.0, read=60.0, write=10.0, connect=3.0), max_retries=0).bind(
            response_format= {
                "type": "json_object"
            }
        )

    return _json_llm

def get_docdb():
    global docdb
    global pinecone_index
    global _record_manager

    logger = lib_logging.get_logger()

    if not docdb:
        db_collection_name = "amirdocs"

        db_connection_string = os.getenv(f"{COMPANY_ENV}_DOCDB_DATABASE")
        record_manager_connection_string = os.getenv(f"{COMPANY_ENV}_RECORDMANAGER_DATABASE")

        logger.debug(f"Connecting to docdb: {db_connection_string} and record manager: {record_manager_connection_string}")

        docdb = PGVector(
            embedding_function=get_embedding_fn(),
            collection_name=db_collection_name,
            connection_string=db_connection_string
        )

        namespace = f"pgvector/{db_collection_name}"
        _record_manager = SQLRecordManager(namespace, db_url=record_manager_connection_string)

        _record_manager.create_schema()


        # # initialize pinecone
        # pinecone.init(
        #     api_key=os.getenv("PINECONE_API_KEY"),  # find at app.pinecone.io
        #     environment=os.getenv("PINECONE_ENV"),  # next to api key in console
        # )

        # pinecone_index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))
        # docdb = Pinecone(pinecone_index, get_embedding_fn(), "text")


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


def add_docs(docs, source, doc_type):
    logger = lib_logging.get_logger()
    docdb = get_docdb()
    global _record_manager

    try:
        logger.debug(f"Adding {len(docs)} docs to index")
        for doc in docs:
            if not doc.metadata.get('id'):
                raise RuntimeError(f"Document does not have an id")
            if not doc.metadata.get('created_at') or type(doc.metadata.get('created_at')) != int:
                raise RuntimeError(f"Document {doc.metadata.get('id')} does not have a valid created_at timestamp")

            if doc_type is None:
                if not doc.metadata.get('type'):
                    raise RuntimeError(f"Document {doc.metadata.get('id')} does not have a valid type and none specified")
            else:
                if not doc.metadata.get('type'):
                    doc.metadata['type'] = doc_type

            if source is None:
                if not doc.metadata.get('source'):
                    raise RuntimeError(f"Document {doc.metadata.get('id')} does not have a valid source and none specified")
            else:
                if not doc.metadata.get('source'):
                    doc.metadata['source'] = source

        res = index(
            docs,
            _record_manager,
            docdb,
            cleanup=None,
            source_id_key="source"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error loading document into db: {e}")
        raise RuntimeError(f"Error loading document into db: {e}")