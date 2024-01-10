import sys
import dotenv
from ..lib.lib_logging import get_logger, setup_logging
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level

from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from ..lib import lib_gdrive
from ..lib import lib_docdb

dotenv.load_dotenv()
setup_logging()
logger = get_logger()
COMPANY_ENV = None

import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm


from langchain_core.documents import Document

from langchain_community.document_loaders.base import BaseLoader
from itertools import islice
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from ..lib.loaders import slack_loader




def process_and_load_document(docs):
    try:
        logger.debug(f"Processing and loading documents {docs}")
        lib_docdb.add_docs(docs)
        return True
    except Exception as e:
        logger.error(f"Error loading document: {e}")
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

def load_slack_data(slack_zip_path, slack_workspace_url, max_workers=10):
    """
    Load Slack data from the given zip file path and load it into the document database.
    :param slack_zip_path: Path to the Slack export zip file.
    :param slack_workspace_url: URL of the Slack workspace for proper doc sources.
    :param max_workers: Maximum number of threads for concurrent processing.
    :return: None
    """
    try:
        loader = slack_loader.SlackDirectoryLoader(slack_zip_path, slack_workspace_url)
        docs = loader.load()

        # Splitting docs into batches of 10
        doc_batches = batch(docs, 5)

        # Adding docs in batches
        for batch_docs in doc_batches:
            lib_docdb.add_docs(list(batch_docs))

        logger.info("Completed loading Slack documents into the database.")

    except Exception as e:
        logger.error(f"Error loading Slack data: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python script.py <path_to_slack_zip> <slack_workspace_url>")
        sys.exit(1)

    lib_docdb.set_company_environment("CJ")

    slack_zip_path = sys.argv[1]
    slack_workspace_url = sys.argv[2]
    nworkers = int(sys.argv[3])
    load_slack_data(slack_zip_path, slack_workspace_url, nworkers)