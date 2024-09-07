#!/usr/bin/env python3

import logging
import re
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
def split(text_value, query_cfg):

    output = text_value

    if splitby := query_cfg.get("split-by"):
    
        if char_separators := splitby.get("char-separators", []):
            regexPattern = '|'.join(char_separators)
            output = re.split(regexPattern, text_value)

    if lineregex := query_cfg.get("line-regex"):
        if not isinstance(text_value, str):
            logger.error(f"input was expecting string and got '{type(text_value)}'")
            return None
        output = []
        for line in text_value.splitlines():
            if match := re.match(lineregex, line):
                if "group" in query_cfg:
                    group = query_cfg.get("group")
                else:
                    # By default, we are expecting the last group to be the matching one
                    group = match.lastindex
            
                output.append(match.group(group))

    #return [i for i in _trim(output) if len(i) > 0]
    
    # Maintain the properties of the input pstr in the output
    return [pstr(i, properties = text_value.properties) for i in _trim(output) if len(i) > 0]

# Returns all values that match.  Returned values are unchanged.
def match(text_value, query_cfg):

    output = ""

    if lineregex := query_cfg.get("line-regex", {}):
        if not isinstance(text_value, str):
            logger.error(f"input was expecting string and got '{type(text_value)}'")
            return None
        output = []
        for line in text_value.splitlines():
            if re.match(lineregex, line):
                # We are expecting the last group to be the matching one
                output.append(line)

    return output

# Returns all values that match.  Returned values are unchanged.
def replace(input, query_cfg):

    output = None

    if isinstance(input, list):
        output = [replace(i, query_cfg) for i in input]

    if isinstance(input, str):
        output = input

        if match_value := query_cfg.get("match"):
            if replacement_value := query_cfg.get("replacement"):
                if input == match_value:
                    output = replacement_value

    return output

def _wrapper(text_fn, input_value, query_cfg):
    
    if isinstance(input_value, dict) and "value" in input_value:
            
        output = text_fn(input_value["value"], query_cfg)
    else:
        output = text_fn(input_value, query_cfg)

    if isinstance(output, dict):
        return
            
# text_dispatch_table = {
#     "text-split": lambda input_value, query_cfg: _wrapper(split, input_value, query_cfg),
#     "text-match": lambda input_value, query_cfg: _wrapper(match, input_value, query_cfg),
#     "text-replace": lambda input_value, query_cfg: _wrapper(replace, input_value, query_cfg),
# }

text_dispatch_table = {
    "text-split": split,
    "text-match": match,
    "text-replace": replace
}