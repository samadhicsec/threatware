#!/usr/bin/env python3

import os, io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as SvcAcctCredentials

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive.readonly']

def _getCredentials(connection):

    if "credentials-file" in connection:
        # Use the credentials file to create credentials
    
        creds = None
        #token_path = str(Path(__file__).absolute().parent.joinpath("token.json"))
        #credentials_path = str(Path(__file__).absolute().parent.joinpath("credentials.json"))
        token_path = connection.get("token-file")
        credentials_path = connection.get("credentials-file")

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    else:

        creds = SvcAcctCredentials.from_service_account_info(connection, scopes=SCOPES)

    return creds

def connect(connection:dict):

    api_key = _getCredentials(connection)
    
    service = build('drive', 'v3', credentials=api_key)

    return service

def exists(cservice, doc_id):
    
    return True

def history(confluence, page_id):
    
    return None

def read(service, doc_id, version=''):
    
    request = service.files().export_media(fileId=doc_id, mimeType='text/html')

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        logger.debug("Download %d%%." % int(status.progress() * 100))
    
    document = fh.getvalue().decode('utf-8')

    return document

