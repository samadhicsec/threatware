#!/usr/bin/env python3
"""
Utility methods for models (dict->list->dict structures)
"""

import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def recurse(model, key_value_callback, list_entry_callback):
    """
    Recurses through a model calling callback functions on every dict key/value and list entry

    Returns: None, if the callbacks don't terminate recursion early, otherwise it returns the callback return value that terminated recursion
    """

    def _stub_callback(*args):
        return True, None

    if key_value_callback is None:
        key_value_callback = _stub_callback
    if list_entry_callback is None:
        list_entry_callback = _stub_callback

    def _internal_recurse(model, value):
        # The return value of this function is only changed if teh recursion exits early, otherwise the input 'value' is returned

        if isinstance(model, dict):
            for dict_key, dict_value in model.items():
                if key_value_callback is not None:
                    keep_going, return_value = key_value_callback(dict_key, dict_value, value)
                    if not keep_going:
                        return keep_going, return_value
                            
                if isinstance(dict_value, dict) or isinstance(dict_value, list):
                    keep_going, loop_return_value = _internal_recurse(dict_value, value)
                    if not keep_going:
                        return keep_going, loop_return_value

        if isinstance(model, list):
            for list_entry in model:
                if isinstance(list_entry, dict) or isinstance(list_entry, list):
                    keep_going, return_value = list_entry_callback(list_entry, value)
                    if not keep_going:
                        return keep_going, return_value
                    keep_going, loop_return_value = _internal_recurse(list_entry, return_value)
                    if not keep_going:
                        return keep_going, loop_return_value
        
        return True, value
    
    _, return_value =_internal_recurse(model, None)

    return return_value