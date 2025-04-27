#!/usr/bin/env python3
"""
Validates whether a value is a date
"""

import logging
import dateutil.parser 
from dateutil.parser import ParserError
from threatware.data.key import key as Key

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:

    try:
        parsed = dateutil.parser.parse(value)
        #key.addProperty(references['validator-tag'], config["output_text_valid"].format(key, value))
        return True
    except (ParserError, OverflowError):
        #key.addProperty(references['validator-tag'], config["output_text_invalid"].format(key, value))
        return False

    return False