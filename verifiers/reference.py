#!/usr/bin/env python3
"""
Helper methods for dealing with references
"""

from cmath import log
import logging
import re
import data.find as find
from data.key import key as Key
import utils.match as match
import utils.tags as tags
import utils.keymaster as keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


# def get_ref_tag_parts(reftag:str):

#     # Split tag into parts
#     tag_parts = reftag.split("/")

#     if len(tag_parts) < 3 or len(tag_parts) > 4:
#         return None, None, None, None

#     tag_prefix = tag_parts[0]
#     tag_data_tag_name = tag_parts[1]
#     tag_field_tag_name = tag_parts[2]
#     tag_comparison = "equals"
#     if len(tag_parts) == 4:
#         tag_comparison = tag_parts[3]

#     return tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison

# def check_tag_comparison(tag_tuple, compare_value, compare_to_key, compare_to_value, callback, callback_config, only_callback = False):

#     tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

#     if not only_callback and tag_comparison == "" or tag_comparison == "equals":
#         if match.equals(compare_value, compare_to_value):
#             return True
#     if not only_callback and tag_comparison == "endswith":
#         if match.endswith(compare_value, compare_to_value):
#             return True
#     else:
#         if callback is not None:
#             return callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value)    

#     return False

def get_references(model, ref_type, ref_key, ref_value, callback, callback_config):
    """
    Gets all reference tag references a value that matches/compares to the passed in value

    References are returned from the location where the tag points to i.e. a data section

    Parameters
    ----------
    model : dict
        The model where the dict keys are a data.key.Key that supports having tags
    ref_type : str
        The type of reference e.g. "ref", "tref"
    ref_key : data.key.Key
        The Key with the reference tag attached to it
    ref_value : str 
        The value of the key with the reference tag
    callback : function(callback_config, comparison_str, compare_to_value, compare_value) -> bool
        A callback to do do custom comparisons between referenced values and ref_value
    callback_config : dict
        Configuration for callback

    Returns
    -------
    list(tuple) : 
        - The reference tag that references a value that matches the value.  
        - The key of the reference
        - The value of the reference
    """
    logger.info(f"Entering get_references")
    referenced = []
    for tag in ref_key.getTags():

        tag_tuple = tags.get_quad_tag_parts(tag)
        tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

        if ref_type != tag_prefix:
            # We are only looking at tags with the desired prefix
            continue

        # Get the table to search for the value
        table_key, table_value = find.key_with_tag(model, tag_data_tag_name)

        if table_key is None:
            logger.warning(f"Reference '{tag}' included a data tag location of '{tag_data_tag_name}' which could not be found")
            continue

        result_list = find.keys_with_tag(table_value, tag_field_tag_name)

        if len(result_list) == 0:
            logger.debug(f"Reference '{tag}' included a field tag location of '{tag_field_tag_name}' which could not be found")
            continue

        for found_key, found_value in result_list:
            if tags.check_tag_comparison(tag_tuple, ref_value, found_key, found_value, callback, callback_config):
                found_referenced = (tag, found_key, found_value)
                if found_referenced not in referenced:
                    referenced.append(found_referenced)
    
    logger.info(f"Exiting get_references")
    return referenced

def check_reference(model, ref_type, ref_key, ref_value, callback, callback_config):

    return len(get_references(model, ref_type, ref_key, ref_value, callback, callback_config)) > 0
    

def check_reference_row(row, ref_type, ref_key, ref_value, callback, callback_config, only_callback):
    """
    Checks whether a reference tag references a value in a row that matches/compares to the passed in value

    References are returned from the passed in row

    Parameters
    ----------
    row : dict
        The row data to look for the reference
    ref_type : str
        The type of reference e.g. "ref", "tref"
    ref_key : data.key.Key
        The Key with the reference tag attached to it
    ref_value : str 
        The value of the key with the reference tag
    callback : function(callback_config, tag, compare_to_value, compare_value) -> bool
        A callback to do do custom comparisons between referenced values and ref_value
    callback_config : dict
        Configuration for callback
    only_callback: bool
        Only use the callback to do the comparison, and ignore default comparison methods

    Returns
    -------
    str : The reference tag that references a value that matches the value.  'None' if no match found.
    """

    # Need a Key so we can verify the data section
    row_id_key, row_id_data = find.key_with_tag(row, "row-identifier")
    row_data_tag_name = keymaster.get_data_tag_for_key(row_id_key)

    for tag in ref_key.getTags():

        tag_tuple = tags.get_quad_tag_parts(tag)
        tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

        if ref_type != tag_prefix:
            # We are only looking at tags with the desired prefix
            continue

        # Check the tag_data_tag_name matches the data for the row
        if row_data_tag_name == tag_data_tag_name:

            result_list = find.keys_with_tag(row, tag_field_tag_name)

            if len(result_list) == 0:
                logger.warning(f"Reference '{tag}' included a field tag location of '{tag_field_tag_name}' which could not be found")
                continue

            for found_key, found_value in result_list:
                if tags.check_tag_comparison(tag_tuple, ref_value, found_key, found_value, callback, callback_config, only_callback):
                    return tag
    
    return None

# def get_prefixed_tag(prefix:str, target_key) -> list:

#     output = []

#     for tag in target_key.getTags():
#         if tag.startswith(prefix):
#             output.append(tag)

#     return output

# def get_values_for_tags(model, ref_tag_list:list, output:dict):

#     for tag in ref_tag_list:

#         tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tags.get_quad_tag_parts(tag)

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

# def get_matching_tags(ref_key, prefix, data_name, field_name, comparison):

#     output = []

#     for tag in ref_key.getTags():
        
#         tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tags.get_quad_tag_parts(tag)

#         if tag_prefix == prefix or prefix == "":
#             if tag_data_tag_name == data_name or data_name == "":
#                 if tag_field_tag_name == field_name or field_name == "":
#                     if tag_comparison == comparison or comparison == "":
#                         output.append(tag)

#     return output

def get_reference_descriptions(model:dict, ref_type:str, ref_key:Key):

    description = []

    # For each tag with the prefix (so if any match, it verifies)
    for tag in ref_key.getTags():

        tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tags.get_quad_tag_parts(tag)

        if ref_type != tag_prefix:
            # A key might have several other tags unrelated to references
            continue
        
        # Get the table to search for the value
        table_key, table_value = find.key_with_tag(model, tag_data_tag_name)
        if table_key is not None:
            if (sectionKey := keymaster.get_section_for_key(table_key)) is None:
                logger.warning(f"Could not find section property for '{table_key.name}'")
                section_name = table_key.name
            else:
                section_name = sectionKey.getProperty("section")
        else:
            logger.warning(f"Could not find data table with tag '{tag_data_tag_name}'")
            section_name = tag_data_tag_name
        
        field_key, _ = find.key_with_tag(table_value, tag_field_tag_name)
        field_colname = None
        if field_key is not None:
            field_colname = field_key.getProperty("colname")
        if field_colname is None:
            logger.debug(f"Could not find data field with tag '{tag_field_tag_name}'")
            field_colname = tag_field_tag_name

        if match.is_empty(tag_comparison):
            tag_comparison = "equals"

        section_field_tuple = (section_name, field_colname, tag_comparison)
        if section_field_tuple not in description:
            description.append(section_field_tuple)

    output = [{'table':tablename, 'column':colname, 'match-type':tag_comparison} for tablename, colname, tag_comparison in description]

    return output