#!/usr/bin/env python3
"""
Utility methods for string matching
"""

import logging
from utils import transform
from utils.model import recurse

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# def c14n(value:str, transform_fn = None) -> str:
#     if transform_fn is not None:
#         value = transform_fn(value)
#     return value.casefold().strip()

# Returns the 'possible' value if 'str_to_match' equals 'possible' string/one of list of strings
def get_equals(str_to_match:str, possible, transform_fn = None) -> str:

    if str_to_match is None:
        str_to_match = ""
    if possible is None:
        possible = ""

    if isinstance(str_to_match, str):
        str_to_match_c14n = transform.c14n(str_to_match, transform_fn)
    else:
        logger.warning(f"Expecting a string to match but '{str_to_match}' is a '{type(str_to_match)}'")

    if isinstance(possible, str):
        possible = [possible]

    for possible_match in possible:
        if possible_match is None:
            possible_match = ""
        if isinstance(possible_match, str):
            possible_match_c14n = transform.c14n(possible_match, transform_fn)
        if str_to_match_c14n == possible_match_c14n:
            return possible_match

    return None

# Returns True if 'str_to_match' equals 'possible' string/one of list of strings
def equals(str_to_match:str, possible, transform_fn = None) -> bool:
    return get_equals(str_to_match, possible, transform_fn) is not None

# Returns True if 'str_to_match' is empty
def is_empty(str_to_match:str) -> bool:

    return equals(str_to_match, "")

# Returns True if all descendents of 'data' are empty
def is_empty_recursive(data:object) -> bool:

    def _inner_is_empty(key, value, context):
        if isinstance(value, str):
            if is_empty(value):
                return True, True
            else:
                return False, False

    _, result = recurse(data, _inner_is_empty, None)

    return result

def endswith(str_to_match:str, ends_with) -> bool:

    str_to_match = transform.c14n(str_to_match)

    if isinstance(ends_with, str):
        ends_with = [ends_with]
    if not isinstance(ends_with, list):
        logger.error(f"'ends_with' parameter must be string or list of strings, not '{type(ends_with)}'")

    does_end_with = False
    for ending_str in ends_with:
        if str_to_match.endswith(transform.c14n(ending_str)):
            does_end_with = True
            break

    return does_end_with
    

# Returns True if string starts with 'start_with' string/one of list of strings, and ends with 'ends_with' string/one of list of strings
def starts_ends(str_to_match:str, starts_with, ends_with) -> bool:

    str_to_match = transform.c14n(str_to_match)

    if isinstance(starts_with, str):
        starts_with = [starts_with]
    if isinstance(ends_with, str):
        ends_with = [ends_with]
    if not isinstance(starts_with, list):
        logger.error(f"'starts_with' parameter must be string or list of strings, not '{type(starts_with)}'")
    if not isinstance(ends_with, list):
        logger.error(f"'ends_with' parameter must be string or list of strings, not '{type(ends_with)}'")

    does_start_with = False
    for starting_str in starts_with:
        if str_to_match.startswith(transform.c14n(starting_str)):
            does_start_with = True
            break
    
    does_end_with = False
    for ending_str in ends_with:
        if str_to_match.endswith(transform.c14n(ending_str)):
            does_end_with = True
            break

    return does_start_with and does_end_with

def get_contains(str_to_match:str, values, transform_fn = None) -> bool:
    """
    Returns the value, if any of the values are contained in str_to_match
    """

    str_to_match = transform.c14n(str_to_match, transform_fn)

    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        logger.error(f"'values' parameter must be string or list of strings, not '{type(values)}'")
    
    for value_str in values:
        if str_to_match.find(transform.c14n(value_str, transform_fn)) != -1:
            return value_str
            
    return None

def contains(str_to_match:str, values, transform_fn = None) -> bool:
    """
    Returns True, if any of the values are contained in str_to_match
    """
    return get_contains(str_to_match, values, transform_fn) is not None
