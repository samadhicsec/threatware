#!/usr/bin/env python3
"""
Validates whether the output of a string method matches an expected value
"""

import logging
from utils import match
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:

    if (method := config.get("method", None)) is None:
        logger.error("Validator config did not have a 'method' key")
        return False
    
    if (expected_result := config.get("expected-result", None)) is None:
        logger.debug("Validator config did not have an 'expected-result' key. Result of method used directly.")

    parameter = config.get("input-parameter", None)
    if parameter is not None and not isinstance(parameter,str):
        logger.error("Validator config for 'input-parameter' must be a string (if specified)")
        return False

    if method == "equals":
        result = match.equals(value, expected_result)
    elif method == "notequals":
        result = not match.equals(value, expected_result)
    elif method == "isempty":
        result = match.is_empty(value)
    elif method == "isnotempty":
        result = not match.is_empty(value)
    elif method == "count":
        if parameter is None:
            logger.error("String method 'count' requires an 'input-parameter' to be configured")
            return False
        result = value.count(parameter) == expected_result
    elif method == "startswith":
        if parameter is None:
            logger.error("String method 'startswith' requires an 'input-parameter' to be configured")
            return False
        result = value.startswith(parameter)
    elif method == "endswith":
        if parameter is None:
            logger.error("String method 'endswith' requires an 'input-parameter' to be configured")
            return False
        result = value.endswith(parameter)
    elif method == "find":
        if parameter is None:
            logger.error("String method 'find' requires an 'input-parameter' to be configured")
            return False
        result = value.find(parameter) == expected_result
    elif method == "isalnum":
        result = value.isalnum()
    elif method == "isalpha":
        result = value.isalpha()
    elif method == "isascii":
        result = value.isascii()
    elif method == "isdecimal":
        result = value.isdecimal()
    elif method == "isdigit":
        result = value.isdigit()
    elif method == "islower":
        result = value.islower()
    elif method == "isnumeric":
        result = value.isnumeric()
    elif method == "isprintable":
        result = value.isprintable()
    elif method == "isspace":
        result = value.isspace()
    elif method == "istitle":
        result = value.istitle()
    elif method == "isupper":
        result = value.isupper()
    else:
        logger.error(f"Validator config 'method' key of '{method}' is not a supported string method")
        return False

    # if expected_result is not None:
    #     return_result = expected_result == result
    # else:
    #     return_result = result

    return result