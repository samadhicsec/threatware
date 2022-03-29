#!/usr/bin/env python3

import os
import configparser
import logging
import convertors.confluence_convertor.reader as reader
import convertors.html_convertor.query as query
from convertors.html_convertor.convertor import doc_to_model

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def _getCredentials(config_file = '~/.atlassian', section = 'DEFAULT'):
    config = configparser.ConfigParser()
    config.read(os.path.expanduser(config_file))
    
    if not config.has_option(section, 'url'):
        logger.warning("No 'url' field found in the '{}' config file in section '{}'".format(config, section))
    if not config.has_option(section, 'username'):
        logger.warning("No 'username' field found in the '{}' config file in section '{}'".format(config, section))
    if not config.has_option(section, 'api_token'):
        logger.warning("No 'api_token' field found in the '{}' config file in section '{}'".format(config, section))
    
    return config.get(section, 'url'), config.get(section, 'username'), config.get(section, 'api_token')

def convert(connection:dict, mapping:dict, doc_identifers:dict):

    # Establish connection to document location
    doc_store = reader.connect(connection)

    if doc_store == None:
        logger.error("Connection details inappropriately formatted")

    # Check the document exists
    if not reader.exists(doc_store, doc_identifers.get('id', '')):
        logger.error("Document with id = {} does not exist".format(doc_identifers.get('id', '')))

    # Read the document into a string
    document = reader.read(doc_store, doc_identifers.get('id', ''))

    # Read the document as html xml element
    # This will return an lxml element at the root node which is the 'html' tag
    query_document = query.get_document(document)

    # Convert the document
    return doc_to_model(query_document, mapping)

