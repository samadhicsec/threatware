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

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def config():

    return convertors_config.config()


def _output(config:dict):

    return FormatOutput(config.get("output", {}))


def convert(config:dict, execution_env, scheme:dict, doc_location:str):

    logger.info("Entering convert")
    
    output = _output(config)

    try: 
        if scheme['document-storage'] == "confluence":
            model = convertors.confluence_convertor.convertor.convert(execution_env.getConfluenceConnectionCredentials(), scheme, {"id":doc_location})
        elif scheme['document-storage'] == "googledoc":
            model = convertors.gdoc_convertor.convertor.convert(execution_env.getGoogleCredentials(), scheme, {"id":doc_location})
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
        
        return convert(config, execution_env, scheme, doc_location)
    
    except ConvertError as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting convert_template")

    return output

# def tojson(model):

#     return jsonpickle.encode(model, unpicklable=False)

# if __name__ == "__main__":

#     parser = argparse.ArgumentParser(description='Threat Model Convertor')

#     parser.add_argument('-s', '--scheme', required=True, help='Identifier for the scheme to load')
#     parser.add_argument('-d', '--docloc', required=True, help='Identifier for the document to verify')
#     args = parser.parse_args()

#     output = convert(args.scheme, args.docloc)

#     print(output)
