#!/usr/bin/env python3

import logging
from threatware.utils.location import Location
import threatware.convertors.confluence_convertor.reader as reader
import threatware.convertors.html_convertor.query as query
from threatware.convertors.html_convertor.convertor import doc_to_model
from threatware.response.response import Response

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

def convert(config:dict, connection:dict, mapping:dict, location:Location, store_doc:bool):

    if location.isDocumentProvided():
        document = location.getDocument()
    elif location.isLocationIDProvided():
        # Establish connection to document location
        doc_store = reader.connect(connection)

        if doc_store == None:
            logger.error("Connection details inappropriately formatted")

        # Check the document exists
        if not reader.exists(doc_store, location.getLocationID()):
            logger.error("Document with id = {} does not exist".format(location.getLocationID()))

        # Read the document into a string
        document = reader.read(doc_store, location.getLocationID())
    else:
        logger.error("No document or document location ID provided")
        raise Exception("No document or document location ID provided")  

    # Store the string
    if store_doc:
        Response.setDocument(document)

    # Read the document as html xml element
    # This will return an lxml element at the root node which is the 'html' tag
    query_document = query.get_document(document, mapping)

    # Convert the document
    return doc_to_model(config, query_document, mapping)

