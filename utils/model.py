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
            # We have found a row of data
            for dict_key, dict_value in model.items():
                if key_value_callback is not None:
                    # The purpose of this callback is to do something to every entry in a row or determine something about the row
                    keep_going, return_value = key_value_callback(dict_key, dict_value, value)
                    if not keep_going:
                        return keep_going, return_value
                            
                # If an entry of a row is itself a complex structure we recurse into it
                if isinstance(dict_value, dict) or isinstance(dict_value, list):
                    keep_going, loop_return_value = _internal_recurse(dict_value, return_value)
                    if not keep_going:
                        return keep_going, loop_return_value

        if isinstance(model, list):
            # We have found a table
            for list_entry in model:
                if isinstance(list_entry, dict) or isinstance(list_entry, list):
                    # The purpose of this callback is do something with an entire row
                    keep_going, return_value = list_entry_callback(list_entry, value)
                    if not keep_going:
                        return keep_going, return_value
                    keep_going, loop_return_value = _internal_recurse(list_entry, return_value)
                    if not keep_going:
                        return keep_going, loop_return_value
        
        return True, value
    
    _, return_value =_internal_recurse(model, None)

    return return_value


# In order to find the location of certain tagged data we need to tag keys with the rows they are in
def assign_row_identifiers(model):

    def _key_value_callback(dict_key, dict_value, rowIDKey):
        # We dont know where in the hierarchy we are, but for dicts we just add the rowIDKey
        if rowIDKey is not None:
            dict_key.addProperty("rowID", rowIDKey)

        return True, rowIDKey

    def _list_entry_callback(list_entry, rowIDKey):
        if isinstance(list_entry, dict):
            local_rowIDKey = rowIDKey
            # Rows are stored as dict
            for dict_key, dict_value in list_entry.items():
                if dict_key.hasTag("row-identifier"):
                    #print(f"Found key tagged with 'row-identifier - {dict_key}")
                    # We found a "row-identifier" for an entry in this row, let's use that from now on
                    local_rowIDKey = dict_key
                    # We need to report errors with the value for the "row-identiifer" key, so let's store the value as a property of the key
                    dict_key.addProperty("value", dict_value)
                    # We need to be able to get sibling data in a row, so also store a reference to the whole row against the 'row-identifier' key
                    dict_key.addProperty("row", list_entry)

                    # There should only be 1 row-identifier per row
                    break
            # Let's assign the the rowIDKey to all elements of this row (the 'row-identifier' field might not have been the first)
            # This will include child elements as well
            return True, local_rowIDKey
        else:
            # Not a row so recurse using existing rowIDKey
            return True, rowIDKey

    return recurse(model, _key_value_callback, _list_entry_callback)


# In order to find the location of certain tagged data we need to tag keys with their parent keys
def assign_parent_keys(model):

    def _key_value_callback(dict_key, dict_value, parentKey):
        # For every key, assign it a parentKey
        dict_key.addProperty("parentKey", parentKey)
        # If we recurse further, then this dict_key becomes the parentKey for descendants
        return True, dict_key

    def _list_entry_callback(list_entry, parentKey):
        # Descendants of a list entry share the same parentKey, so just pass it along
        return True, parentKey
        
    return recurse(model, _key_value_callback, _list_entry_callback)
    