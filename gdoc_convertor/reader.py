#!/usr/bin/env python3

import io
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def connect(api_key):
    
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

