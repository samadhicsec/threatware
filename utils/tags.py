#!/usr/bin/env python3
"""
Utility methods for tags
"""
import re

import logging
from utils import match

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def get_quad_tag_parts(reftag:str):
    """
    Return a 4-tuple given a tag
    """

    # Split tag into parts
    tag_parts = reftag.split("/")

    if len(tag_parts) < 3 or len(tag_parts) > 4:
        return None, None, None, None

    tag_prefix = tag_parts[0]
    tag_context_name = tag_parts[1]
    tag_value_name = tag_parts[2]
    tag_comparison = "equals"
    if len(tag_parts) == 4:
        tag_comparison = tag_parts[3]

    return tag_prefix, tag_context_name, tag_value_name, tag_comparison

def check_tag_comparison(tag_tuple, compare_value:str, compare_to_key, compare_to_value, callback, callback_config, only_callback = False):
    """
    Using the tag comparison method, check if two key values compare
    """

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    if not only_callback and tag_comparison == "" or tag_comparison == "equals":
        if match.equals(compare_value, compare_to_value):
            return True
    if not only_callback and tag_comparison == "endswith":
        if match.endswith(compare_value, compare_to_value):
            return True
    else:
        if callback is not None:
            return callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value)    

    return False

def get_prefixed_tag(prefix:str, target_key) -> list:
    """
    Return all the tags on a key with the given prefix
    """

    output = []

    for tag in target_key.getTags():
        if tag.startswith(prefix):
            output.append(tag)

    return output


# Return a list tags of all tags matching the regex
def tags_matching_regex(key, regex_str:str, compiled_regex = None):
    """ 
    Returns a list of tags with all tags that match the regular expression
    """

    if compiled_regex is None:
         compiled_regex = re.compile(regex_str)

    tags_list = []

    for tag in key.getTags():
        if compiled_regex.search(tag) is not None:
            tags_list.append(tag)
    
    return tags_list


# def get_values_for_tags(model, ref_tag_list:list, output:dict):
#     """

#     """

#     for tag in ref_tag_list:

#         tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = get_quad_tag_parts(tag)

#         for key_entry, value_entry in find.keys_with_tag(model, tag):
#             if isinstance(value_entry, str):
#                 if match.is_empty(value_entry):
#                     continue
#                 tag_dict_key = tag_data_tag_name + "/" + tag_field_tag_name
#                 if output.get(tag_dict_key) is None:
#                     output[tag_dict_key] = []
#                 if value_entry not in output[tag_dict_key]:
#                     output[tag_dict_key].append(value_entry)
#             else:
#                 logger.warning(f"Reference value '{tag}' did not point to a string")

#     return                

def get_matching_tags(key, prefix, context_name, value_name, comparison):
    """
    Return all tags that match the passed in tag parts
    """

    output = []

    for tag in key.getTags():
        
        tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = get_quad_tag_parts(tag)

        if tag_prefix == prefix or prefix == "":
            if tag_data_tag_name == context_name or context_name == "":
                if tag_field_tag_name == value_name or value_name == "":
                    if tag_comparison == comparison or comparison == "":
                        output.append(tag)

    return output