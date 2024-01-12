import dotenv
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level
from tqdm import tqdm
from langchain_core.documents import Document

from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from itertools import islice
from ..lib import lib_gdrive
from ..lib import lib_docdb

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
    details['send_date'] = send_date
    details['original_message'] = original_message

    logger.debug(f"Returning from {details['from']} to {details['to']} at {details['send_date']} with subject {details['subject']}")
    return details

def load_emails(email_details):
    # logger.debug(f"Loading e-mail into db {email_details['id']} - {email_details['from']} - {email_details['to']} - {email_details['subject']}") 
    try:
        docs = []

        for email in email_details:
            # print(email)
            timestamp = int(email['send_date'].timestamp())

            metadata = {
                'id': email['id'],
                'type': 'email',
                'source': 'gmail',
                'email_id': email['id'],
                'thread_id': email['threadId'],
                'from_address': email['from'],
                'send_date': timestamp,
                'created_at': timestamp,
                'to_address': email['to'] if email['to'] else '',
                'subject': email['subject'] if email['subject'] else '',
                'name': f"FROM: {email['from']}\nTO: {email['to']}\nSUBJECT: {email['subject'] if email['subject'] else 'No Subject'}" 
            }

            docs.append(Document(
                page_content=email['original_message'],
                metadata=metadata
            
            ))

        lib_docdb.add_docs(docs, 'gmail', 'email')
        # logger.debug(f"Loaded e-mail")
        return email_details
    except Exception as e:
        logger.error(f"Error loading e-mail into db: {e}")

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

def gmail_pipeline(max_documents):
    loaded_email_ids = []
    # list(lib_emaildb.get_email_ids())
    emails = get_gmail_messages(max_documents)

    # Split emails into batches of size 5
    batch_size = 25
    email_batches = list(batch(emails, batch_size))

    succeeded = 0
    failed = 0
    # Process each batch of emails and show progress with tqdm
    for batch_emails in tqdm(email_batches, desc="Processing Emails", total=len(email_batches)):
        try:
            details_batch = []
            for email in batch_emails:
                details = get_message_details(email)
                # logger.info(f"Email details {details['id']} - {details['from']} - {details['to']} - {details['subject']}")
                details_batch.append(details)

            if load_emails(details_batch):
                succeeded += 1
            else:
                failed += 1
        except Exception as exc:
            logger.error(f"One or more emails generated an exception: {exc}")
            failed += 1

        logger.info(f"Successfully loaded {succeeded * batch_size} emails failed {failed * batch_size}")

    logger.info(f"Successfully loaded {len(emails)} emails")

def run_pipeline(company_env, max_documents):
    global COMPANY_ENV
    COMPANY_ENV = company_env
    lib_docdb.set_company_environment(COMPANY_ENV)
    gmail_pipeline(max_documents)
