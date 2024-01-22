import argparse
import src.pipeline.gmail_pipeline as gmail_pipeline
import src.lib.lib_logging as lib_logging
import logging
import dotenv
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level
import json
from tqdm import tqdm
from langchain_core.documents import Document

from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from itertools import islice
from ..lib import lib_gdrive
from ..lib import lib_docdb

googleapiclient_logger = logging.getLogger('googleapiclient.discovery_cache')
googleapiclient_logger.setLevel(logging.WARNING)

dotenv.load_dotenv()
setup_logging()
logger = get_logger()
COMPANY_ENV = None

def get_gmail_messages(max_documents):
    lib_gdrive.gmail_authenticate(COMPANY_ENV)
    logger.info(f"Getting emails sent from me")
    emails_sent = lib_gdrive.list_messages('me', query='from:me', batch_size=max_documents)

    return emails_sent

def get_message_details(email):
    try:
        lib_gdrive.gmail_authenticate(COMPANY_ENV)
        details = lib_gdrive.get_message('me', email['id'])
    except Exception as e:
        logger.error(f"Error getting message details: {e} {type(e)}")
        raise e

    try:
        subject, body, from_address, to_address, send_date, original_message = lib_gdrive.parse_subject_body(details)
    except Exception as e:
        logger.error(f"Error parsing subject body: {e} {type(e)}")
        raise e

    details['subject'] = subject
    details['body'] = body
    details['from'] = from_address
    details['to'] = to_address
    details['send_date'] = int(send_date.timestamp())
    details['original_message'] = original_message

    logger.debug(f"Returning from {details['from']} to {details['to']} at {details['send_date']} with subject {details['subject']}")
    return details



def save_to_jsonl(email_details, filename):
    """
    Save email details to a JSONL file, overwriting existing contents.
    :param email_details: List of email details to save.
    :param filename: Name of the file to save to.
    """
    with open(filename, 'w') as file:
        for email in email_details:
            json_line = json.dumps(email)
            file.write(json_line + '\n')


def gmail_pipeline(max_documents, output_file):
    emails = get_gmail_messages(max_documents)
    email_details = [get_message_details(email) for email in tqdm(emails, desc="Processing Emails")]

    # Save email details to specified JSONL file
    save_to_jsonl(email_details, output_file)

    logger.info(f"Successfully processed {len(emails)} emails and saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Gmail pipeline for a specific company.')
    parser.add_argument('company', choices=['cj', 'fc'], help='Specify the company environment ("cj" or "fc").')
    parser.add_argument('max_documents', type=int, help='Maximum number of documents to load.')
    parser.add_argument('output_file', type=str, help='Output JSONL file to save email details.')
    args = parser.parse_args()

    COMPANY_ENV = args.company.upper()
    gmail_pipeline(args.max_documents, args.output_file)
