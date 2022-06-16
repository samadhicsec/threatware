#!/usr/bin/env python3

import os
from pathlib import Path
import os.path
import logging
import convertors.gdoc_convertor.reader as reader
import convertors.html_convertor.query as query
from convertors.html_convertor.convertor import doc_to_model
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive.readonly']

# def _getCredentials():
    
#     creds = None
#     token_path = str(Path(__file__).absolute().parent.joinpath("token.json"))
#     credentials_path = str(Path(__file__).absolute().parent.joinpath("credentials.json"))

#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.
#     if os.path.exists(token_path):
#         creds = Credentials.from_authorized_user_file(token_path, SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 credentials_path, SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open(token_path, 'w') as token:
#             token.write(creds.to_json())

#     return creds

def convert(connection:dict, mapping:dict, doc_identifers:dict):

    # Establish connection to document location
    doc_store = reader.connect(connection)

    # TODO Check the document exists
    
    # Read the document into a string
    document = reader.read(doc_store, doc_identifers.get('id', ''))

    # Read the document as html xml element
    # This will return an lxml element at the root node which is the 'html' tag
    query_document = query.get_document(document)

    # Convert the document
    return doc_to_model(query_document, mapping)
