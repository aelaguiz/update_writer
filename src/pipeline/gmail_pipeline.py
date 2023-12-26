import dotenv
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level
from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from ..lib import lib_gmail
from ..lib import lib_emaildb

dotenv.load_dotenv()
setup_logging()
logger = get_logger()
COMPANY_ENV = None

def get_gmail_messages(loaded_email_ids):
    service = lib_gmail.gmail_authenticate(COMPANY_ENV)
    logger.info(f"Getting emails sent from me")
    emails_sent = lib_gmail.list_messages(service, 'me', query='from:me', batch_size=15000)

    emails = []
    for email in emails_sent:
        if email['id'] not in loaded_email_ids:
            emails.append(email)
    
    return emails

def get_message_details(email):
    try:
        service = lib_gmail.gmail_authenticate(COMPANY_ENV)
        details = lib_gmail.get_message(service, 'me', email['id'])
    except Exception as e:
        logger.error(f"Error getting message details: {e} {type(e)}")
        raise e

    try:
        subject, body, from_address, to_address, send_date, original_message = lib_gmail.parse_subject_body(details)
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
    logger.debug(f"Loading e-mail into db {email_details['id']} - {email_details['from']} - {email_details['to']} - {email_details['subject']}") 
    lib_emaildb.add_email(email_details)
    logger.debug(f"Loaded e-mail")
    return email_details


def gmail_pipeline(nworkers):
    loaded_email_ids = list(lib_emaildb.get_email_ids())
    emails = get_gmail_messages(loaded_email_ids)

    with ThreadPoolExecutor(max_workers=nworkers) as executor:
        # Create a future for each email for getting details
        future_to_email = {executor.submit(get_message_details, email): email for email in emails}
        
        # Store futures for loading emails
        load_email_futures = []

        # Process each email and show progress with tqdm
        for future in tqdm(as_completed(future_to_email), total=len(future_to_email), desc="Processing Emails"):
            email = future_to_email[future]
            try:
                details = future.result()
                # Submit the loading task and store its future
                load_future = executor.submit(load_emails, details)
                load_email_futures.append(load_future)
                logger.debug(f"Email details {details['id']} - {details['from']} - {details['to']} - {details['subject']}")
            except Exception as exc:
                logger.error(f"{email['id']} generated an exception: {exc}")

        # Wait for all load email tasks to complete and show progress
        for future in tqdm(as_completed(load_email_futures), total=len(load_email_futures), desc="Loading Emails"):
            pass


def run_pipeline(company_env, nworkers):
    global COMPANY_ENV
    COMPANY_ENV = company_env
    lib_emaildb.set_company_environment(COMPANY_ENV)
    gmail_pipeline(nworkers)
