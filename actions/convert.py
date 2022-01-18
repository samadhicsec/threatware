#!/usr/bin/env python3
"""
Converts a Threat Model document into a model
"""

import os, logging
from pathlib import Path
import jsonpickle
import argparse
from utils.load_yaml import yaml_file_to_dict
from schemes.schemes import load_scheme
import confluence_convertor.convertor
import gdoc_convertor.convertor
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def convert(scheme:dict, doc_location:str):
   
    if scheme['document-storage'] == "confluence":
        output = confluence_convertor.convertor.convert({}, scheme, {"id":doc_location})
    elif scheme['document-storage'] == "googledoc":
        output = gdoc_convertor.convertor.convert({}, scheme, {"id":doc_location})
    else:
        logger.error("Unknown document type '{}'".format(scheme['document-storage']))

    return output

def convert_template(scheme:dict, doc_location:str):

    if not doc_location:
        doc_location = scheme['template-id']
        if not doc_location:
            logger.error("No template document location provided as input or defined in the scheme")
    
    return convert(scheme, doc_location)

def tojson(model):

    return jsonpickle.encode(model, unpicklable=False)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Threat Model Convertor')

    parser.add_argument('-s', '--scheme', required=True, help='Identifier for the scheme to load')
    parser.add_argument('-d', '--docloc', required=True, help='Identifier for the document to verify')
    args = parser.parse_args()

    output = convert(args.scheme, args.docloc)

    print(output)
