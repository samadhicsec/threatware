#!/usr/bin/env python3

import logging
import re
import urllib.parse
from utils.property_str import pstr

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# Remove prefix and suffix whitespace
def _trim(value):
    output = value
    
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        output = [_trim(i) for i in value]

    return output

# Returns values split by different possible methods
def extract(input, query_cfg):

    if input is None:
        return None

    output = input

    if regex := query_cfg.get("regex"):
        if not isinstance(input, str):
            logger.error(f"Input was expecting string and got '{type(input)}'")
            return None
        
        if match := re.match(regex, input):
            if "group" in query_cfg:
                group = query_cfg.get("group")
            else:
                # By default, we are expecting the last group to be the matching one
                group = match.lastindex
        
            output = match.group(group)

    return pstr(_trim(output), properties = input.properties)

# Returns all values that match.  Returned values are unchanged.
def match(input, query_cfg):

    if input is None:
        return None

    output = ""

    if regex := query_cfg.get("regex"):
        if not isinstance(input, str):
            logger.error(f"Input was expecting string and got '{type(input)}'")
            return None
        if re.match(regex, input):
            # We are expecting the last group to be the matching one
            output = input

    return output

# Returns all values that match.  Returned values are unchanged.
def replace(input, query_cfg):

    if input is None:
        return None

    output = None

    if not isinstance(input, str):
        logger.error(f"Input was expecting string and got '{type(input)}'")
        return None

    output = input

    if match_value := query_cfg.get("match"):
        if replacement_value := query_cfg.get("replacement"):
            if input == match_value:
                output = pstr(replacement_value, properties = input.properties)

    return output

def url_decode(input, query_cfg):
    """ Expects input to be a string and outputs the string URL decoded """

    if input is None:
        return None

    output = None

    if not isinstance(input, str):
        logger.error(f"Input was expecting string and got '{type(input)}'")
        return None

    output = pstr(urllib.parse.unquote(input), properties = input.properties)

    return output

value_dispatch_table = {
    "value-extract":extract,
    "value-match":match,
    "value-replace":replace,
    "value-urldecode":url_decode
}