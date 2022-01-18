#!/usr/bin/env python3

import logging
import re

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

    return _trim(output)

# Returns all values that match.  Returned values are unchanged.
def match(input, query_cfg):

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

    output = None

    if not isinstance(input, str):
        logger.error(f"Input was expecting string and got '{type(input)}'")
        return None

    output = input

    if match_value := query_cfg.get("match"):
        if replacement_value := query_cfg.get("replacement"):
            if input == match_value:
                output = replacement_value

    return output

value_dispatch_table = {
    "value-extract":extract,
    "value-match":match,
    "value-replace":replace,
}