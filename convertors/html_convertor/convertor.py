#!/usr/bin/env python3

import logging
import data.value
import convertors.html_convertor.query as query

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# Will add a list of dicts to output, 1 for each list member in the unordered list
def _parse_unordered_list(mapping, content, output):

    if not isinstance(content, list):
        logger.warning("Expected content to be 'list', got '{}' instead".format(type(content)))
        return

    for item in content:
        entry = {}
        for kv_map in mapping:
            entry[kv_map["key"]] = query.get_document_value(item, kv_map["value"]["query"])
        output.append(entry)

    return

def _merge_table_row(main_row, merge_row):

    # Look through merge row, adding or appending to main_row
    for entry in merge_row.keys():
        # Add to main_row
        if isinstance(merge_row[entry], list):
            if entry not in main_row.keys():
                main_row[entry] = merge_row[entry]
            else:
                # Unpack lists and create their concatenation
                main_row[entry] = [*main_row[entry], *merge_row[entry]]
        elif isinstance(merge_row[entry], dict):
            if entry not in main_row.keys():
                main_row[entry] = merge_row[entry]
            else:
                _merge_table_row(main_row[entry], merge_row[entry])
        else:
            main_row[entry] = merge_row[entry]

    return

def _parse_row_table_row(mapping, row, output, previous_row = {}):

    # Expecting row to be a list (cols).
    if not isinstance(row, list):
        logger.warning("Expected content to be 'list', got '{}' instead".format(type(row)))
        return

    table_row = {}
    merge_key = None
    # Loop through the list of map entries
    for kv_map in mapping:
        if "query" in kv_map["value"]:
            # This mapping is looking for a value, so get the value from the table row
            table_row[kv_map["key"]] = query.get_table_entry(row, kv_map["value"]["query"])
            # Potentially the value is empty so we may want to inherit the value from the previous row
            if not table_row[kv_map["key"]] and "inherit-row-above-if-empty" in kv_map["value"] and kv_map["value"]["inherit-row-above-if-empty"]:
                table_row[kv_map["key"]] = query.get_table_entry(previous_row, kv_map["value"]["query"])
                # Need to set the current row value so subsequent rows can potentially use it
                query.set_table_entry(row, kv_map["value"]["query"], table_row[kv_map["key"]])
            # Check whether the values we are mapping will be a new entry, or merged with an existing entry - we'll do this later in this method
            if "merge_on_match" in kv_map["value"] and kv_map["value"]["merge_on_match"]:
                merge_key = kv_map["key"]
        elif "mapping" in kv_map["value"]:
            # This mapping is wants to map a set of information from the row to a single parent key
            table_row[kv_map["key"]] = []
            _parse_row_table_row(kv_map["value"]["mapping"], row, table_row[kv_map["key"]])
        
    # Check if we need to merge the content of this wih an existing row
    if merge_key is not None:
        match_found = False
        # Try to find a match
        for row in output:
            if row[merge_key] == table_row[merge_key]:
                _merge_table_row(row, table_row)
                match_found = True
                break
        if not match_found:
            logger.warning("Found a mapping '{}' that should cause rows to merge, but didn't find row to merge".format(merge_key))
    else:
        # Just add as a new row
        output.append(table_row)

    return


# Will add a list of dicts to output, 1 for each row in the table
def _parse_row_table(mapping, content, output):

    # Expecting content to be a list (rows) of lists (cols).  First list is the table headers
    if not isinstance(content, list):
        logger.warning("Expected content to be 'list', got '{}' instead".format(type(content)))
        return

    # Dump the header row
    table = content[1:]
    
    previous_row = {}
    for row in table:
        _parse_row_table_row(mapping, row, output, previous_row)
        previous_row = row
        
    return

# For a given row with n columns where the 1st col is the header column, this will update the output
# with a list of length n-1 where each entry is a dict
def _parse_col_table_row(mapping, row, row_index, output):

    # Expecting row to be a list (cols).
    if not isinstance(row, list):
        logger.warning("Expected content to be 'list', got '{}' instead".format(type(row)))
        return

    # TODO could generalise this and have the mapping declare header columns

    # The number of output dicts should be number of cols - 1, because the first col is the header column
    while len(output) < len(row) - 1:
        output.append([])
    
    for col_index in range(1,len(row)):

        # We output to different locations depending on the column, so ultimately all data in a given column
        # gets written to the same location
        output_list = output[col_index - 1]
        output_dict = {}

        # Loop through the list of map entries
        for kv_map in mapping:
            if "query" in kv_map["value"]:
                value = query.get_constrained_table_entry(row, kv_map["value"]["query"], row_index, col_index)
                if value is not None:
                    output_dict[kv_map["key"]] = value
                #if query.col_index_defined(kv_map["value"]["query"]):
                    # This mapping requires a specific column
                #    output_dict[kv_map["key"]] = query.get_table_entry(row, kv_map["value"]["query"])    
                #else:
                    # This mapping wants the current column
                #    output_dict[kv_map["key"]] = query.get_row_entry_by_col_index(row, col_index)

            elif "mapping" in kv_map["value"]:
                # This mapping is wants to map a set of information from the row to a single parent key
                output_dict[kv_map["key"]] = []
                _parse_row_table_row(kv_map["value"]["mapping"], row, output_dict[kv_map["key"]])
                #logger.warning("Column tables do not support nested mappings, ignoring")
        
        output_list.append(output_dict)


    return

# Will add a list of dicts to output.  A dict for every column.
def _parse_col_table(mapping, content, output, header_row):

    # Expecting content to be a list (rows) of lists (cols).
    if not isinstance(content, list):
        logger.warning("Expected content to be 'list', got '{}' instead".format(type(content)))
        return

    table = content
    if header_row:
        # Skip that row
        table = content[1:]
    
    for row_index, row in enumerate(table):
        _parse_col_table_row(mapping, row, row_index, output)
        
    return

def _parse_content(map_definition, document, output):

    if isinstance(map_definition, dict):
        # Process definition
        meta_section = map_definition["meta"]
        content_section = map_definition["content"]
        mapping = map_definition["mapping"]

        #output["section-name"] = meta_section["friendly-name"]

        # Get document content
        #content = query.get_document_section(document, content_section["query"])
        
        if content_section["content-type"]["markup-type"] == "ul":
            # Get document content
            content = query.get_document_list_items(document, content_section["query"])
            _parse_unordered_list(mapping, content, output)
        if content_section["content-type"]["markup-type"] == "table":
            # Get document content
            content = query.get_document_row_table(document, content_section["query"])
            _parse_row_table(mapping, content, output)
        if content_section["content-type"]["markup-type"] == "col-table":
            # Get document content
            content = query.get_document_row_table(document, content_section["query"])
            _parse_col_table(mapping, content, output, content_section["content-type"].get("header-row", False))

    elif isinstance(map_definition, list):
        for definition in map_definition:
            _parse_content(definition, document, output)

    return

def _process_query(query_def, input):

    query_type = query_def.get("type")

    if query_type == "html-ul":
        # Get document content
        content = query.get_document_list_items(input, query_def)
        return content
    if query_type == "html-table":
        # Get document content
        content = query.get_document_row_table(input, query_def)
        return content
    if query_type == "html-table-remove-header-row":
        # Get document content
        content = query.get_remove_table_header_row(input, query_def)
        return content
    if query_type == "html-table-row":
        # Get document content
        content = query.get_table_entry(input, query_def)
        return content
    if query_type == "html-split-table":
        # Get document content
        content = query.get_split_table(input, query_def)
        return content
    if query_type == "html-table-transpose":
        # Get document content
        content = query.get_transposed_table(input, query_def)
        return content

    logger.warning("Could not process query of type '{}'".format(query_type))
    return None

# The output of processing content is always a list or value
def _get_data(get_data_def, document):

    get_data_defs = []

    if isinstance(get_data_def, dict) and get_data_def:
        # We have just 1 query
        #if (query := get_data_def.get("query")):    # If None is returned then it evaluates to False
        get_data_defs.append(get_data_def)
    elif isinstance(get_data_def, list) and get_data_def:
        get_data_defs = get_data_def

    # Process each query.  Note, if we have no queries, we return the document
    logger.debug("Executing {} queries".format(len(get_data_defs)))
    data = document
    for query_def in get_data_defs:
        data = _process_query(query_def.get("query", {}), data)

    return data

def _parse_data_map(data_map, document):

    # If there is a get-data section use that to extract the data we want to map
    get_data_def = data_map.get("get-data",{})
    
    # Get the data to pass to the map.  
    data = _get_data(get_data_def, document)

    # If there is a map-data section we'll use that to map data to output
    map_data_def = data_map.get("map-data", [])

    if len(map_data_def) == 0:
        return data

    output_data_def = data_map.get("output-data", {})
    output_data_type = output_data_def.get("type", "list")
    if output_data_type == "dict":
        output = {}
    else:
        output = []
    

    if isinstance(data, list):
        output_list = []
        # If get_data returns a list, then we map_data each item in the list
        for list_index, list_item in enumerate(data):
            output_dict = {}
            for key_value in map_data_def:
                key = key_value["key"]
                logger.debug("Mapping data to '{}'".format(key))
                value_def = key_value["value"]
                if isinstance(value_def, dict):
                    # Each mapping needs to receive the list, the list index to process, current output
                    value = _parse_data_map(value_def, list_item)
                    output_dict[key] = value
            logger.debug("Appending output {}".format(output_dict))
            output_list.append(output_dict)
        
        if output_data_type == "dict":
            output = output_list[0]
        else:
            output = output_list
    else:
        output_dict = {}
        # If get_data DOES NOT returns a list, then we map_data just the data
        for key_value in map_data_def:
            key = key_value["key"]
            logger.debug("Mapping data to '{}'".format(key))
            value_def = key_value["value"]
            if isinstance(value_def, dict):
                # Each mapping needs to receive the list, the list index to process, output
                value = _parse_data_map(value_def, data)
                output_dict[key] = value
        logger.debug("Appending output {}".format(key, output_dict))
        output = output_dict

    return output

def doc_to_model(document, mapping):
    
    map = mapping['map']

    tm = {}
    tm["meta"] = {}

    try:
        #tm = _parse_data_map(mapping['map'], document)
        tm = data.value.parse(mapping['map'], document)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    # Parse details
    #details_map = map["details"]
    #tm_details_model = []
    #_parse_content(details_map, document, tm_details_model)
    #tm["details"] = tm_details_model

    # Parse version history
    #version_history_map = map["version-history"]
    #tm_version_history = []
    #_parse_content(version_history_map, document, tm_version_history)
    #tm["version-history"] = tm_version_history

    # Parse scope
    #scope_map = map["scope"]
    #tm_scope = []
    #_parse_content(scope_map, document, tm_scope)
    #tm["scope"] = tm_scope

    # Parse system

    # Parse references
    #references_map = map["references"]
    #tm["meta"]["references"] = {}
    #tm["meta"]["references"]["friendly-name"] = references_map["meta"]["friendly-name"]
    #tm_reference_model = []
    #_parse_content(references_map, document, tm_reference_model)
    #tm["references"] = tm_reference_model

    # Parse Components
    #components_map = map["components"]
    #tm_components_model = []
    #_parse_content(components_map, document, tm_components_model)
    #tm["components"] = tm_components_model

    # Parse Assets

    # Parse Operations
    #operational_map = map["operational-security"]
    #tm_operations_model = []
    #_parse_content(operational_map, document, tm_operations_model)
    #tm["operational-security"] = tm_operations_model

    # Parse Threats and Controls

    return tm

# def convert(connection:dict, mapping:dict, doc_identifers:dict):

#     # Establish connection to document location
    
#     # Check the document exists
    
#     # Read the document into a string
#     #document = reader.read(doc_store, doc_identifers.get('id', ''))

#     # Read the document as html xml element
#     # This will return an lxml element at the root node which is the 'html' tag
#     #query_document = query.get_document(document)

#     # Convert the document
#     return _doc_to_model(query_document)

# if __name__ == "__main__":

#     tm = convert({}, {"id":"65538"})
#     print(tm)