#!/usr/bin/env python3

import logging
import convertors.html_convertor.query
import utils.text_query
import utils.value_query

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def _process_query(query_def, input):

    query_type = query_def.get("type")

    if query_type in convertors.html_convertor.query.html_dispatch_table:
        # Get document content
        content = convertors.html_convertor.query.html_dispatch_table[query_type](input, query_def)
        return content

    if query_type in utils.text_query.text_dispatch_table:
        # Get document content
        content = utils.text_query.text_dispatch_table[query_type](input, query_def)
        return content
    
    if query_type in utils.value_query.value_dispatch_table:
        # Get document content
        content = utils.value_query.value_dispatch_table[query_type](input, query_def)
        return content

    logger.error(f"Could not process query of type '{query_type}'")
    return None

# The output of processing content is always a list or value
def parse(get_data_def, input):

    logger.debug(f"Entering get.parse to process {get_data_def}")

    get_data_defs = []

    if isinstance(get_data_def, dict) and get_data_def:
        # We have just 1 query
        #if (query := get_data_def.get("query")):    # If None is returned then it evaluates to False
        get_data_defs.append(get_data_def)
    elif isinstance(get_data_def, list) and get_data_def:
        get_data_defs = get_data_def

    # Process each query.  Note, if we have no queries, we return the input
    logger.debug(f"Executing {len(get_data_defs)} queries")
    data = input
    for query_def in get_data_defs:
        data = _process_query(query_def.get("query", {}), data)

    logger.debug(f"Leaving get.parse having processed {get_data_def}")

    return data