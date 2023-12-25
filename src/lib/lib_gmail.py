import os
import pickle
import re
import base64
from email import message_from_string
from email.utils import parsedate_to_datetime
from email.policy import default
from flanker import mime
from email.parser import Parser
from bs4 import BeautifulSoup
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from . import lib_logging

logger = lib_logging.get_logger()

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def gmail_authenticate(app_id):
    creds_file = os.getenv(f"{app_id}_SECRET")
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists(f'{app_id}_token.pickle'):
        with open(f'{app_id}_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(f'{app_id}_token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def list_messages(service, user_id, query='', batch_size=100):
    try:
        logger.debug(f'Listing messages with query: {query}')
        response = service.users().messages().list(userId=user_id, q=query, maxResults=batch_size).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        # Check if the number of messages is already at or above the batch size
        while 'nextPageToken' in response and len(messages) < batch_size:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token, maxResults=batch_size).execute()
            messages.extend(response['messages'])
            # Reduce the number of messages to the batch size if it exceeds
            if len(messages) > batch_size:
                messages = messages[:batch_size]
                break

        return messages
    except Exception as error:
        print(f'An error occurred: {error}')
        return None



def parse_subject_body(message):
    subject = None
    body = None
    from_address = None
    to_address = None
    send_date = None

    try:
        # Decode the raw email data
        raw_email_data = base64.urlsafe_b64decode(message['raw']).decode('utf-8')
        email_message = message_from_string(raw_email_data, policy=default)

        # Extract subject, from, and to addresses
        subject = email_message['subject']
        from_address = email_message['from']
        to_address = email_message['to']
        date_string = email_message['date']

        if date_string:
            send_date = parsedate_to_datetime(date_string)
    except Exception as e:
        logger.error(f"Failed to parse subject, from, to: {e} {type(e)}")
        raise e

    try:
        # Get the message body
        if email_message.is_multipart():
            for part in email_message.walk():
                # Find the text/plain part
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8')
                    break
        else:
            body = email_message.get_payload(decode=True).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to parse body: {e} {type(e)}")
        raise e

    original_message = None
    try:
        original_message = parse_out_original_message(body)
    except Exception as e:
        logger.error(f"Failed to parse out original message: {e} {type(e)}")
        logger.error(body)
        raise e

    return subject, body, from_address, to_address, send_date, original_message

def parse_out_original_message(email_content):
    # Remove headers
    email_content = re.sub(r'From:.*\n?', '', email_content)
    email_content = re.sub(r'To:.*\n?', '', email_content)
    email_content = re.sub(r'Subject:.*\n?', '', email_content)
    email_content = re.sub(r'Date:.*\n?', '', email_content)

    # Remove quoted replies and signatures
    # email_content = re.sub(r'On.*wrote:.*', '', email_content)
    # email_content = re.sub(r'--\n.*', '', email_content, flags=re.DOTALL)

    # Remove any leading/trailing whitespace
    email_content = email_content.strip()

    return email_content

def get_message(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
        # print(f'Message snippet: {message["snippet"]}')
        return message
    except Exception as error:
        print(f'An error occurred: {error}')