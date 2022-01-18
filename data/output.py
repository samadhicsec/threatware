#!/usr/bin/env python3

import logging

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


post_processor_dispatch_table = {
    "inherit-row-above-if-empty":_inherit_row_above_if_empty,
    "value-replace": _value_replace
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