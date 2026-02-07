#!/usr/bin/env python3
"""
Converts a Threat Model document into a model
"""

import logging
from threatware.utils.error import ConvertError, ProviderError
from threatware.utils.output import FormatOutput
from threatware.utils.location import Location
from threatware.schemes.schemes import get_document_storage, get_default_template
from threatware.convertors import convertors_config
import threatware.convertors.confluence_convertor.convertor
import threatware.convertors.gdoc_convertor.convertor

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

def config():

    return convertors_config.config()


def _output(config:dict):

    return FormatOutput(config.get("output", {}))


def convert(config:dict, execution_env, scheme:dict, location:Location, store_doc:bool=True):

    logger.info("Entering convert")
    
    output = _output(config)

    scheme_doc_storage = get_document_storage(scheme)

    try: 
        if scheme_doc_storage == "confluence":
            model = threatware.convertors.confluence_convertor.convertor.convert(config, execution_env.getConfluenceConnectionCredentials(), scheme, location, store_doc)
        elif scheme_doc_storage == "googledoc":
            model = threatware.convertors.gdoc_convertor.convertor.convert(config, execution_env.getGoogleCredentials(), scheme, location, store_doc)
        else:
            logger.error(f"Unknown document storage type '{scheme_doc_storage}'")
            raise ConvertError("unknown-doc-storage", {"doc_storage":scheme_doc_storage})

        output.setSuccess("success", {}, model)

    except (ConvertError, ProviderError) as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting convert")

    return output


def convert_template(config:dict, execution_env, scheme:dict, location:Location):

    logger.info("Entering convert_template")

    output = _output(config)

    try: 

        if not location.isDocumentProvided() and not location.isLocationIDProvided():
            template_location = get_default_template(scheme)
            if not template_location:
                logger.error("No template document location provided as input or defined in the scheme")
                raise ConvertError("no-template-doc", {})
        return convert(config, execution_env, scheme, location, store_doc=False)
    
    except ConvertError as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting convert_template")

    return output

