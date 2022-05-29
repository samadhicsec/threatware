#!/usr/bin/env python3

import logging
from data.key import key as Key
import utils.match as match
import utils.model as model

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def parse(output_def):

    output_data_type = output_def.get("type", "list")
    if output_data_type == "dict":
        output = {}
    else:
        output = []

    return output

def assign(output_def, output_data):

    output_data_type = output_def.get("type", "list")
    if output_data_type == "dict":
        if isinstance(output_data, dict):
            return output_data
        if isinstance(output_data, list):
            if len(output_data) > 1:
                logger.warning(f"dict output specified, but input was of length {len(output_data)} (>1). Just using first.")
            return output_data[0]

        logger.warning(f"Could not convert output data type '{type(output_data)}' to dict")
        return None
    else:
        return output_data

def _inherit_row_above_if_empty(proc_def, output_data):

    # output_data needs to be a list
    if not isinstance(output_data, list):
        logger.warning(f"Cannot run post-processor 'inherit-row-above-if-empty' on output data of type '{type(output_data)}', needs to be a list")
        return output_data

    # Get the key to look for
    if key := proc_def.get("key"):
        row_above_value = ""
        for row_item in output_data:

            if isinstance(row_item, dict):
                if key in row_item:
                    if isinstance(row_item[key], str):
                        value = row_item[key].strip()
                        if value == "":
                            # Replace value with value from row above
                            row_item[key] = row_above_value
                        else:
                            # We found a value for the current row, let's remember it for future rows
                            row_above_value = value

    return output_data

def _remove_empty_rows(proc_def, output_data):

    # output_data needs to be a list
    if not isinstance(output_data, list):
        logger.warning(f"Cannot run post-processor 'remove-empty-rows' on output data of type '{type(output_data)}', needs to be a list")
        return output_data

    # Get list of any columns to ignore the value of
    ignore_list = []
    if proc_def:
        ignore_list = proc_def.get("ignore-keys", [])

    def _inner_is_empty(key, value, context):
        if isinstance(value, str):
            if key.name not in ignore_list:
                if not match.is_empty(value):
                    return False, False

        return True, True

    new_output_data = []
    for row in output_data:
        empty = model.recurse(row, _inner_is_empty, None)
        # False will be returned if a non-empty found (we add these to the output), otherwise None will be returned if all empty
        if empty is False:
            new_output_data.append(row)

    return new_output_data

def _value_replace(proc_def, output_data):

    # output_data needs to be a str
    if not isinstance(output_data, str):
        logger.warning(f"Cannot run post-processor 'value_replace' on output data of type '{type(output_data)}', needs to be a string")
        return output_data

    # Get the key to look for
    for matches in proc_def:
        if match := matches.get("match"):
            if replacement := matches.get("replacement"):
                if output_data == match:
                    output_data = replacement
                    break   # exit early on first match

    return output_data

def _extract_col_name(colname:str) -> str:
    """
    Extracts all data before line boudnaries and just returns that as the column header.  This allows help text to be placed in the same table cell as a column header, but ignored.
    """
    if not isinstance(colname, str):
        return ""

    return colname.splitlines()[0]

def _remove_header_row(proc_def, output_data):
    """
    Removes the first row from the output data (must be a list).  Assumes values are column header names and sets the 'colname' property on all descendant 
    Keys.
    """

    # output_data needs to be a list
    if not isinstance(output_data, list):
        logger.warning(f"Cannot run post-processor 'remove-header-row' on output data of type '{type(output_data)}', needs to be a list")
        return output_data
    if len(output_data) == 0:
        logger.debug(f"Cannot run post-processor 'remove-header-row' on output data of no entries")
        return output_data

    # Get the list of col header names
    colnames = []
    for colname in output_data[0].values():
        # The value might not be a string, it might be a dictionary, but that dict should just have 1 entry
        if isinstance(colname, str):
            colnames.append(_extract_col_name(colname))
        else:
            if isinstance(colname, list) and len(colname) > 0:
                # Look at the first entry in the list, which should be a dict
                colname = colname[0]
            if isinstance(colname, dict):
                if len(colname.values()) == 0:
                    logger.warning(f"Expected 1 column name in dict '{colname}'.  Setting to empty")
                    colnames.append("")
                else:
                    # Table rows that aren't read in as straight values but instead are processed further, can have multiple values
                    #if len(colname.values()) > 1:
                    #    logger.warning(f"Expected only 1 column name in dict '{colname}'.  Using first")
                    colnames.append(_extract_col_name(list(colname.values())[0]))
            else:
                logger.warning(f"Unknown column name type of  '{type(colname)}'.  Setting to empty")
                colnames.append("")

    for row in output_data[1:]:
        for rowkey, rowvalue, colname in zip(row.keys(), row.values(), colnames):
            rowkey.addProperty("colname", colname)
            def _set_col_name(entry):

                if isinstance(entry, list):
                    for e in entry:
                        _set_col_name(e)
                if isinstance(entry, dict):
                    for k, v in entry.items():
                        if isinstance(k, Key):
                            k.addProperty("colname", colname)
                        _set_col_name(v)

            _set_col_name(rowvalue)

    return output_data[1:]

post_processor_dispatch_table = {
    "inherit-row-above-if-empty":_inherit_row_above_if_empty,
    "remove-empty-rows": _remove_empty_rows,
    "value-replace": _value_replace,
    "remove-header-row": _remove_header_row
}

def process(output_def, output_data):

    logger.debug(f'Entering: Keys {output_def.keys()}')

    if output_type := output_def.get("type"):
        output_data = assign(output_def, output_data)

    if post_processor := output_def.get("post-processor"):
        logger.debug(f'Found post-processors {post_processor.keys()}')
        # Need to move through the post-processors in order specified in case order matters for processing
        for proc in post_processor.keys():
            if proc in post_processor_dispatch_table:
                output_data = post_processor_dispatch_table[proc](post_processor[proc], output_data)
            else:
                logger.warning(f"Could not find post-processor '{proc}'")

    logger.debug(f'Leaving: Keys {output_def.keys()}')

    return output_data