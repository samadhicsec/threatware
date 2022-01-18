#!/usr/bin/env python3
"""
Test validator
"""

import logging
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:
    key.addProperty(references['validator-tag'], "output")
    return True