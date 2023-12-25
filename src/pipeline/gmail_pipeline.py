import argparse
import asyncio
from prefect import task, flow, unmapped
from prefect.tasks import task_input_hash
from prefect.concurrency.asyncio import concurrency
from ..lib.lib_logging import get_logger, get_run_logger, setup_logging, set_console_logging_level
from ..lib import lib_gmail
from ..lib import lib_emaildb
import dotenv

dotenv.load_dotenv()
setup_logging()
logger = get_logger()

@task
async def get_gmail_messages(loaded_email_ids, company_env):
    logger = get_run_logger()
    logger.debug(f"In get_gmail_messages: {len(loaded_email_ids)}")
    async with concurrency("gmail_get_messages_limit"):
        logger.info("Getting emails from inbox")

        service = lib_gmail.gmail_authenticate(company_env)
        logger.info("Getting emails sent from me")
        emails_sent = lib_gmail.list_messages(service, 'me', query='from:me', batch_size=400)

        emails = [email for email in emails_sent if email['id'] not in loaded_email_ids]
        return emails

@task
async def get_message_details(email, company_env):
    logger = get_run_logger()
    logger.debug(f"In get_message_details: {email['id']}")
    async with concurrency("gmail_get_details_limit", occupy=1):
        logger.debug(f"Passed the concurrency limit: {email['id']}")
        try:
            service = lib_gmail.gmail_authenticate(company_env)
            details = lib_gmail.get_message(service, 'me', email['id'])
            subject, body, from_address, to_address, send_date, original_message = lib_gmail.parse_subject_body(details)
            
            return {
                'subject': subject,
                'body': body,
                'from': from_address,
                'to': to_address,
                'send_date': send_date,
                'original_message': original_message
            }
        except Exception as e:
            logger.error(f"Error getting message details: {e} {type(e)}")
            raise

@task
async def load_emails(email_details):
    logger = get_run_logger()
    logger.debug(f"In load_emails: {email_details['id']} - {email_details['from']} - {email_details['to']} - {email_details['subject']}")
    async with concurrency("gmail_load_emails_limit"):
        logger.debug(f"Loading e-mail into db {email_details['id']} - {email_details['from']} - {email_details['to']} - {email_details['subject']}")
        lib_emaildb.add_email(email_details)
        logger.debug("Loaded e-mail")
        return email_details

@flow
async def gmail_pipeline(company_env):
    logger = get_run_logger()
    loaded_email_ids = list(lib_emaildb.get_email_ids())
    emails = await get_gmail_messages(loaded_email_ids, company_env)

    email_detail_futures = await get_message_details.map(emails, unmapped(company_env))
    for future in email_detail_futures:
        details = await future.result()
    # loaded_emails = await load_emails.map(email_detail_futures)

    # results = []
    # for future in loaded_emails:
    #     details = future.result()
    #     results.append(details)
    #     logger.info(f"Email details {details['id']} - {details['from']} - {details['to']} - {details['subject']}")
    # return results

async def run_pipeline(company_env):
    await gmail_pipeline(company_env)