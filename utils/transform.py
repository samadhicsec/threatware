#!/usr/bin/env python3
"""
Utility methods for transforming strings
"""

import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def c14n(value:str, transform_fn = None) -> str:
    if transform_fn is not None:
        value = transform_fn(value)
    return value.casefold().strip()


def strip(start_char:str, end_char:str):
    """
    Strips everything between the start and end characters/str (inclusive)

    Returns a function.  Designed for use with methods taking transform_fn parameters that end up calling c14n e.g. util.match
    """
    def _strip_context(value:str,start_char:str, end_char:str):

        if(start_char_index := value.find(start_char)) != -1:
            if(end_char_index := value.find(end_char, start_char_index)) != -1:
                return value[:start_char_index] + value[end_char_index + 1:]

        return value

    return lambda val : _strip_context(val, start_char,  end_char)

