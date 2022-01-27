#!/usr/bin/env python3
"""
Validates whether a value matches a regular expression
"""

import logging
from pathlib import Path
import re
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:

    if not (pattern := config.get("pattern", None)):
        logger.error("Validator config did not have a 'pattern' key")
        return False

    try:
        if re.search(pattern, value):
            return True
    except re.error as err:
        logger.error(f"The pattern '{pattern}' passed to the regex validator caused an exception '{err}'")
        return False

    return False