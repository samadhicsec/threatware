#!/usr/bin/env python3

import logging
from threatware.data.data_config import DataConfig
import threatware.data.value
import threatware.convertors.html_convertor.query as query

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

def doc_to_model(config:dict, document:dict, mapping:dict):
    
    tm = {}

    try:
        
        DataConfig.init(config.get("data", {}))

        tm = threatware.data.value.parse(mapping['map'], document)

    except BaseException as err:
        logger.error(f"Unexpected err='{err}', type='{type(err)}'")
        raise

    return tm
