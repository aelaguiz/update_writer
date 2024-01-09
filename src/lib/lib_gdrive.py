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

from diskcache import Cache

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/drive.readonly']

_gmail_service = None
_gdrive_service = None
COMPANY_ENV = None

def gmail_authenticate(company_env):
    global _gmail_service
    global _gdrive_service
    global COMPANY_ENV
    COMPANY_ENV = company_env

    creds_file = os.getenv(f"{COMPANY_ENV}_SECRET")
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists(f'{COMPANY_ENV}_token.pickle'):
        with open(f'{COMPANY_ENV}_token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(f'{COMPANY_ENV}_token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    _gmail_service = build('gmail', 'v1', credentials=creds)
    _gdrive_service = build('drive', 'v3', credentials=creds)

def list_messages(user_id, query='', batch_size=100):
    global COMPANY_ENV
    cache_path = f'./cache_{COMPANY_ENV}'
    with Cache(cache_path) as cache:
        @cache.memoize()
        def _list_messages(user_id, query, batch_size):
            global _gmail_service

            try:
                logger.debug(f'Listing messages with query: {query}')
                response = _gmail_service.users().messages().list(userId=user_id, q=query, maxResults=batch_size).execute()
                messages = []
                if 'messages' in response:
                    messages.extend(response['messages'])

                while 'nextPageToken' in response and len(messages) < batch_size:
                    page_token = response['nextPageToken']
                    response = _gmail_service.users().messages().list(userId=user_id, q=query, pageToken=page_token, maxResults=batch_size).execute()
                    messages.extend(response['messages'])
                    if len(messages) > batch_size:
                        messages = messages[:batch_size]
                        break

                return messages
            except Exception as error:
                print(f'An error occurred: {error}')
                return None

        return _list_messages(user_id, query, batch_size)


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
        subject = email_message.get('subject', '')
        from_address = email_message.get('from', '')
        to_address = email_message.get('to', '')
        date_string = email_message.get('date', '')

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

def get_message(user_id, msg_id):
    global _gmail_service
    global COMPANY_ENV
    cache_path = f'./cache_{COMPANY_ENV}'
    with Cache(cache_path) as cache:
        @cache.memoize()
        def _get_message(user_id, msg_id):
            try:
                message = _gmail_service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
                # print(f'Message snippet: {message["snippet"]}')
                return message
            except Exception as error:
                print(f'An error occurred: {error}')

        return _get_message(user_id, msg_id)

def list_recently_viewed_files(batch_size=100):
    global _gdrive_service
    global COMPANY_ENV

    cache_path = f'./cache_files_{COMPANY_ENV}'
    with Cache(cache_path) as cache:
        @cache.memoize()

        def _list_recently_viewed_files(batch_size):
            mime_types = ("mimeType = 'application/vnd.google-apps.document' or "
                        "mimeType = 'application/vnd.google-apps.spreadsheet' or "
                        "mimeType = 'application/vnd.google-apps.presentation'")
            
            query = f"{mime_types} and trashed = false"


            items = []
            items_collected = 0
            page_token = None
            # Fetch the most recently viewed file_gmail_service
            while items_collected < batch_size:
                # Adjust the page size to fetch the remaining files if fewer than total_files are left
                page_size = min(batch_size - items_collected, 100)  # 100 is the maximum page size for Google Drive API

                results = _gdrive_service.files().list(
                    q=query,
                    orderBy='viewedByMeTime desc', 
                    fields='nextPageToken, files(id, name, viewedByMeTime, mimeType, owners, lastModifyingUser, modifiedTime, createdTime)',
                    pageSize=page_size,
                    pageToken=page_token
                ).execute()

                page_items = results.get('files', [])
                items.extend(page_items)
                items_collected += len(page_items)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            return items

        return _list_recently_viewed_files(batch_size)

def get_file_contents(file_id, file_obj):
    global _gdrive_service
    global COMPANY_ENV
    global COMPANY_ENV

    cache_path = f'./cache_files_{COMPANY_ENV}'
    with Cache(cache_path) as cache:
        @cache.memoize()
        def _get_file_contents(file_id, file_obj):
            mime_type = file_obj['mimeType']

            if "google-apps.document" in mime_type:
                content = _gdrive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
                content = content.decode('utf-8')
                file_obj['gdrive_type'] = 'document'
                file_obj['content'] = content
            elif "google-apps.presentation" in mime_type:
                print("Fetching google slides...")
                content = _gdrive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
                file_obj['gdrive_type'] = 'presentation'
                file_obj['content'] = content.decode('utf-8')
            elif "google-apps.spreadsheet" in mime_type:
                print("Fetching google sheet...")
                content = _gdrive_service.files().export(fileId=file_id, mimeType='text/csv').execute()
                file_obj['gdrive_type'] = 'spreadsheet'
                file_obj['content'] = content.decode('utf-8')

            return file_obj

        return _get_file_contents(file_id, file_obj)