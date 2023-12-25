from prefect import task, flow
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging
from ..lib import lib_gmail
from ..lib import lib_emaildb
import dotenv

dotenv.load_dotenv()

setup_logging()

logger = get_logger()

service = lib_gmail.gmail_authenticate('FC')

@task
def get_gmail_messages(loaded_email_ids):
    emails_sent = lib_gmail.list_messages(service, 'me', query='from:me')

    emails = []
    for email in emails_sent:
        if email['id'] not in loaded_email_ids:
            emails.append(email)
    
    return emails


@task
def get_message_details(email):
    try:
        service = lib_gmail.gmail_authenticate('FC')
        details = lib_gmail.get_message(service, 'me', email['id'])
    except Exception as e:
        logger.error(f"Error getting message details: {e} {type(e)}")
        raise e

    try:
        subject, body, from_address, to_address, original_message = lib_gmail.parse_subject_body(details)
    except Exception as e:
        logger.error(f"Error parsing subject body: {e} {type(e)}")
        raise e

    details['subject'] = subject
    details['body'] = body
    details['from'] = from_address
    details['to'] = to_address
    details['original_message'] = original_message

    logger.debug(f"Returning from {details['from']} to {details['to']} with subject {details['subject']}")
    return details

@task
def load_emails(email_details):
    logger = get_run_logger()

    logger.debug(f"Loading e-mail into db {email_details['id']} - {email_details['from']} - {email_details['to']} - {email_details['subject']}") 

    lib_emaildb.add_email(email_details)

    logger.debug(f"Loaded e-mail")

    return email_details

@flow
def gmail_pipeline():
    loaded_email_ids = list(lib_emaildb.get_email_ids())
    emails = get_gmail_messages(loaded_email_ids)

    email_detail_futures = get_message_details.map(emails)
    loaded_emails = load_emails.map(email_detail_futures)

    for details_future in loaded_emails:
        details = details_future.result()
        logger.info(f"Email details {details['id']} - {details['from']} - {details['to']} - {details['subject']}]")


if __name__ == '__main__':
    logger.info("Starting pipeline")

    gmail_pipeline()