#!/usr/bin/env python3
"""
Converts a Threat Model document into a model
"""

import logging
from utils.error import ConvertError, ProviderError
from utils.output import FormatOutput
from convertors import convertors_config
import convertors.confluence_convertor.convertor
import convertors.gdoc_convertor.convertor
from utils.output import FormatOutput

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def config():

    return convertors_config.config()


def _output(config:dict):

    return FormatOutput(config.get("output", {}))


def convert(config:dict, execution_env, scheme:dict, doc_location:str, store_doc:bool=True):

    logger.info("Entering convert")
    
    output = _output(config)

    try: 
        if scheme['document-storage'] == "confluence":
            model = convertors.confluence_convertor.convertor.convert(config, execution_env.getConfluenceConnectionCredentials(), scheme, {"id":doc_location}, store_doc)
        elif scheme['document-storage'] == "googledoc":
            model = convertors.gdoc_convertor.convertor.convert(config, execution_env.getGoogleCredentials(), scheme, {"id":doc_location}, store_doc)
        else:
            logger.error(f"Unknown document storage type '{scheme['document-storage']}'")
            raise ConvertError("unknown-doc-storage", {"doc_storage":scheme['document-storage']})

        output.setSuccess("success", {}, model)

    except (ConvertError, ProviderError) as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting convert")

    return output


def convert_template(config:dict, execution_env, scheme:dict, doc_location:str):

    logger.info("Entering convert_template")

    output = _output(config)

    try: 

        if not doc_location:
            doc_location = scheme['template-id']
            if not doc_location:
                logger.error("No template document location provided as input or defined in the scheme")
        
        return convert(config, execution_env, scheme, doc_location, store_doc=False)
    
    except ConvertError as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting convert_template")

    return output

