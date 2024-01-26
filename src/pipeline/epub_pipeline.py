import sys
import dotenv
import datetime
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

from ..lib.loaders import epub_loader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python script.py company path_to_books")
        sys.exit(1)


    company = sys.argv[1]
    epub_path = sys.argv[2]

    lib_docdb.set_company_environment(company.upper())

    epub_files = [file for file in os.listdir(epub_path) if file.endswith(".epub")]

    for epub_file in epub_files:
        epub_file_path = os.path.join(epub_path, epub_file)
        logger.info(f"Loding {epub_file_path}")

        loader = epub_loader.EPubLoader(epub_file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=int(2000), chunk_overlap=200, add_start_index=True)
        all_docs = text_splitter.split_documents(docs)

        for doc in all_docs:
            doc.metadata['id'] = doc.metadata['title'] + '-' + str(doc.metadata['start_index'])
            doc.metadata['created_at'] = int(datetime.datetime.now().timestamp())
            doc.metadata['name'] = doc.metadata['title']

        lib_docdb.add_docs(all_docs, source="epub", doc_type="book")
