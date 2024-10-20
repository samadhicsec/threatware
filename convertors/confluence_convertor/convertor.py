#!/usr/bin/env python3

import os
import configparser
import logging
import convertors.confluence_convertor.reader as reader
import convertors.html_convertor.query as query
from convertors.html_convertor.convertor import doc_to_model
from response.response import Response

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def convert(config:dict, connection:dict, mapping:dict, doc_identifers:dict, store_doc:bool):

    # Establish connection to document location
    doc_store = reader.connect(connection)

    if doc_store == None:
        logger.error("Connection details inappropriately formatted")

    # Check the document exists
    if not reader.exists(doc_store, doc_identifers.get('id', '')):
        logger.error("Document with id = {} does not exist".format(doc_identifers.get('id', '')))

    # Read the document into a string
    document = reader.read(doc_store, doc_identifers.get('id', ''))

    # Store the string
    if store_doc:
        Response.setDocument(document)

    # Read the document as html xml element
    # This will return an lxml element at the root node which is the 'html' tag
    query_document = query.get_document(document, mapping)

    # Convert the document
    return doc_to_model(config, query_document, mapping)

