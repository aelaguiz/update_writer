import dotenv
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level
from tqdm import tqdm

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from itertools import islice
from ..lib import lib_gdrive
from ..lib import lib_docdb
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

dotenv.load_dotenv()
setup_logging()
logger = get_logger()
COMPANY_ENV = None

def get_gdrive_files(max_docs):
    lib_gdrive.gmail_authenticate(COMPANY_ENV)
    logger.info(f"Getting my recently viewed docs")
    gdrive_files = lib_gdrive.list_recently_viewed_files(batch_size=max_docs)
    
    logger.debug(f"Found {len(gdrive_files)} files")
    for file in gdrive_files:
        print(file)
        logger.debug(f"File {file['id']} - {file['name']}")

    return gdrive_files

def get_file_contents(file_obj):
    try:
        lib_gdrive.gmail_authenticate(COMPANY_ENV)
        file_obj_with_contents = lib_gdrive.get_file_contents(file_obj['id'], file_obj)
    except Exception as e:
        logger.error(f"Error getting message contents: {e} {type(e)}")
        raise e

    return file_obj_with_contents

def load_files(file_details):
    try:
        docs = []
        for file_obj in file_details:

            metadata = {
                'type': file_obj['gdrive_type'],
                'owners': ", ".join(f['displayName'] for f in file_obj['owners']),
                'name': file_obj['name'],
                'id': file_obj['id'],
                'mime_type': file_obj['mimeType'],
                'source': 'gdrive'
            }

            metadata['created_at'] = int(datetime.fromisoformat(file_obj['createdTime']).replace(tzinfo=None).timestamp())
            metadata['modified_at'] = int(datetime.fromisoformat(file_obj['modifiedTime']).replace(tzinfo=None).timestamp())

            docs.append(Document(
                page_content=file_obj['content'],
                metadata=metadata
            ))
            # logger.debug(f"Adding {file_obj['name']} to index: {metadata}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=5000,
            chunk_overlap=200,
            add_start_index=True
        )

        split_docs = text_splitter.split_documents(docs)
        logger.debug(f"Split {len(docs)} docs into {len(split_docs)} chunks")

        # for doc in split_docs:
        #     logger.debug(f"Adding {doc.metadata['name']} to index: {doc.metadata}: {doc.page_content}")

        lib_docdb.add_docs(split_docs, 'gdrive', None)
        logger.debug(f"Loaded {len(split_docs)} docs")
        return True
    except Exception as e:
        logger.error(f"Error loading docs into db: {e}")
        return False

def batch(iterable, size):
    """
    Split an iterable into batches of a specified size.
    :param iterable: The iterable to split into batches.
    :param size: The size of each batch.
    :return: A generator yielding batches of the specified size.
    """
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            return
        yield batch

def gdrive_pipeline(max_docs):
    files = get_gdrive_files(max_docs)

    # Split emails into batches of size 5
    batch_size = 5
    file_batches = list(batch(files, batch_size))

    succeeded = 0
    failed = 0
    # Process each batch of emails and show progress with tqdm
    for batch_files in tqdm(file_batches, desc="Processing Files", total=len(file_batches)):
        try:
            details_batch = []
            for file_obj in batch_files:
                file_obj_with_contents = get_file_contents(file_obj)
                details_batch.append(file_obj_with_contents)

            if load_files(details_batch):
                succeeded += 1
            else:
                failed += 1
        except Exception as exc:
            logger.error(f"One or more files generated an exception: {exc}")
            failed += 1

        logger.info(f"Successfully loaded {succeeded * batch_size} files failed {failed * batch_size}")

    logger.info(f"Successfully loaded {len(files)} files")

def run_pipeline(company_env, max_docs):
    global COMPANY_ENV
    COMPANY_ENV = company_env
    lib_docdb.set_company_environment(COMPANY_ENV)
    gdrive_pipeline(max_docs)
