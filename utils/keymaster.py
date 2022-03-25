#!/usr/bin/env python3
"""
Utility methods for data.key.Key
"""

import logging
import re
from data import find
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def get_section_for_key(row_key:Key) -> Key:
    if row_key is not None:
        sectionKey = row_key
        while (sectionKey.getProperty("section") is None) and (sectionKey.getProperty("parentKey") is not None):
            sectionKey = sectionKey.getProperty("parentKey")

        if sectionKey.getProperty("section") is not None:
            return sectionKey

    return None

def get_data_tag_for_key(row_key:Key) -> str:
    if row_key is not None:
        sectionKey = row_key
        
        while (len([tag for tag in sectionKey.getTags() if re.search("^.*-data$", tag)]) == 0) and (sectionKey.getProperty("parentKey") is not None):
            sectionKey = sectionKey.getProperty("parentKey")

        data_tag_list = [tag for tag in sectionKey.getTags() if re.search("^.*-data$", tag)]
        if len(data_tag_list) > 0:
            if len(data_tag_list) > 1:
                logger.warning(f"The key '{sectionKey}' should not be members of multiple data sections i.e. '{data_tag_list}'")
            return data_tag_list[0]

    return None

def get_row_identifier_for_key(row_key:Key):

    if row_key is not None:
        if row_key.hasTag("row-identifier"):
            return row_key
        elif row_key.getProperty("rowID") is not None:
            return row_key.getProperty("rowID")

    return None

def get_row_identifiers_for_key(row_key:Key):

    if row_key is not None:
        if row_key.hasTag("row-identifier") or row_key.getProperty("rowID") is not None:
            # It's possible the row_key is the same as the row identifier location, in which case the 
            # "rowID" property will not be set on it (it would be a circular reference)
            rowID_key = row_key.getProperty("rowID")
            if rowID_key is None:
                # row_key must have tag "row-identifier"
                return row_key.name, row_key.getProperty("value")
            else:
                return rowID_key.name, rowID_key.getProperty("value")

    return None, None

def get_column_name_for_key(row_key:Key) -> str:
    return row_key.getProperty("colname")

# def get_row_identifier_key(row_key:Key):

#     row_identifier_key, row_identifier_value = get_row_identifiers_for_key(row_key)

#     parentKeys = []
#     if row_identifier_key is None:
#         tableKey = row_key
#         # Navigate up the parents until we hit a table section
#         while (tableKey.getProperty("section") is None) and (tableKey.getProperty("parentKey") is not None):
#             parentKeys.append(tableKey)
#             tableKey = tableKey.getProperty("parentKey")

#         # Navigate back down, noting the row for the table
#         for row in tableKey.getProperty("value"):

#             def find_child_row(row, index):
#                 if isinstance(row, dict):
#                     row = [row]
#                 for row_entry in row:
#                     for row_key, row_value in row_entry.items():
#                         if row_key is parentKeys[index]:
#                             if index == 0:
#                                 return True
#                             return find_child_row(row_value, index - 1)
#                 return False
            
#             success = find_child_row(row, -1)
#             if success:
#                 row_identifier_key = find.key_with_tag(row, "row-identifier")
#                 return row_identifier_key
#     return None


