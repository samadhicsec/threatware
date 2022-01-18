import logging
import re

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def key_with_tag(model, tag:str):

    if isinstance(model, dict):
        for dict_key, dict_value in model.items():
            if dict_key.hasTag(tag):
                return dict_key, dict_value
            if isinstance(dict_value, dict) or isinstance(dict_value, list):
                found_key, found_value = key_with_tag(dict_value, tag)
                if found_key is not None:
                    return found_key, found_value
    
    if isinstance(model, list):
        for list_entry in model:
            found_key, found_value = key_with_tag(list_entry, tag)
            if found_key is not None:
                return found_key, found_value

    return None, None

# Return a list of tuples (key,value) for all keys with the tag
def keys_with_tag(model, tag:str):

    keys_list = []

    if isinstance(model, dict):
        for dict_key, dict_value in model.items():
            if dict_key.hasTag(tag):
                keys_list.append((dict_key, dict_value))
            if isinstance(dict_value, dict) or isinstance(dict_value, list):
                keys_list.extend(keys_with_tag(dict_value, tag))
    
    if isinstance(model, list):
        for list_entry in model:
            keys_list.extend(keys_with_tag(list_entry, tag))

    return keys_list

# Return a list of tuples (key,value) for all keys with the tag
def keys_with_tag_matching_regex(model, regex_str:str, compiled_regex = None):
    """ 
    Returns a list of tuples (key,value) for all keys with a tag that matches the regular expression

    """

    if compiled_regex is None:
         compiled_regex = re.compile(regex_str)

    keys_list = []

    if isinstance(model, dict):
        for dict_key, dict_value in model.items():
            for tag in dict_key.getTags():
                if compiled_regex.search(tag) is not None:
                    keys_list.append((dict_key, dict_value))
                    break   # We only capture 1 tag.
            if isinstance(dict_value, dict) or isinstance(dict_value, list):
                keys_list.extend(keys_with_tag_matching_regex(dict_value, regex_str, compiled_regex))
    
    if isinstance(model, list):
        for list_entry in model:
            keys_list.extend(keys_with_tag_matching_regex(list_entry, regex_str, compiled_regex))

    return keys_list