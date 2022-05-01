#!/usr/bin/env python3

import logging
from lxml import etree
import lxml.html
from html_table_parser import HTMLTableParser

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

XPATH_FIELD = "xpath"
COLUMN_NUM = "column-num"
ROW_NUM = "row-num"
PROCESS_IGNORE_COLS = "ignore-cols"
PROCESS_REMOVE_HEADER_ROW = 'remove-header-row'
PROCESS_REMOVE_ROWS_IF_EMPTY = "remove-rows-if-empty"
PROCESS_SPLIT_TYPE = "split-type"

def get_document(document_str):

    # Note, can't do much pre-processing of the XML here as the scheme might be referencing something that we might change
    return lxml.html.document_fromstring(document_str)

def get_document_section(document, query_cfg):

    section_list = document.xpath(query_cfg[XPATH_FIELD])

    if len(section_list) == 0:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned no results")
        return None

    if len(section_list) != 1:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned more than 1 result, only using first")

    return section_list[0]

def get_document_list_items(document, query_cfg):

    list_items = document.xpath(query_cfg[XPATH_FIELD])

    logger.debug(f"Query '{query_cfg[XPATH_FIELD]}' return {len(list_items)} elements")

    return list_items

def get_document_value(document, query_cfg) -> str:

    value_list = document.xpath(query_cfg[XPATH_FIELD])

    logger.debug(f"Query '{query_cfg[XPATH_FIELD]}' return {len(value_list)} elements")

    if len(value_list) == 0:
        return None
    if len(value_list) > 1:
        logger.warning(f"Retreived {len(value_list)} document values when 1 was expected.  Using first.")
        
    if not isinstance(value_list[0], str):
        logger.warning(f"Expected results 'str', got '{type(value_list[0])}', for query '{query_cfg[XPATH_FIELD]}'")

    # Despite checking this is a str, it could be a _ElementUnicodeResult, which doesn't serialise to JSON nicely.  So explicitly convert.

    return str(value_list[0])

def _remove_rows_if_empty(proc_def, table_data):

    # output_data needs to be a list
    if not isinstance(table_data, list):
        logger.warning(f"Cannot process 'remove_row_if_empty' on data of type '{type(table_data)}', needs to be a list")
        return table_data

    # Get list of any columns to ignore the value of
    ignore_list = []
    if proc_def:
        ignore_list = proc_def.get(PROCESS_IGNORE_COLS, [])

    new_table_data = []
    for row in table_data:
        test_row = row
        # If there are cols to ignore, then make a copy of the row without those cols
        if len(ignore_list) > 0:
            test_row = [value for count, value in enumerate(row) if count not in ignore_list]
        # Check if any of the values of the row are set
        if any(test_row):
            # At least one is set, so copy ORIGINAL row
            new_table_data.append(row)

    return new_table_data

def get_document_row_table(document, query_cfg):

    # Navigate to the <table> element
    table_list = document.xpath(query_cfg[XPATH_FIELD])

    if len(table_list) == 0:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned no results")
        return []
    elif len(table_list) != 1:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned more than 1 result, only using first")

    table_ele = table_list[0]

    # Parsing a table is much easier if we remove HTML elements that just style the output, and since the output of
    # this method is no longer XML, we know subsequent queries don't rely on these elements.
    # Stripping span doesn't affect content (and Google Docs have A LOT of span elements)
    etree.strip_tags(table_ele, "span")
    # Reluctantly removing 'superscript' elements.  It seems Google Docs will add single letter superscript to elements
    # when you download the doc as HTML, where that text is hihglight as part of a comment.  Lesser of two evils is to 
    # not support 'superscript' elements (as we have to allow a document with comments to be verified)
    etree.strip_elements(table_ele, "sup")
    # Stripping attributes of <p> elements doesn't affect content, but we leave them in because they are usually used
    # like newlines, whcih is what we replace them with further down.
    for ele in table_ele.findall('.//p'):
        etree.strip_attributes(ele, "style")

    # Extract as string
    table_bstr = lxml.html.tostring(table_ele, encoding='unicode')
    # HTMLTableParser will strip all tags from table entries, but sometimes that information is relevant e.g. <p></p> as newlines
    table_str = table_bstr.replace("</p><p>", "\n")

    # Parse as table
    p = HTMLTableParser()
    p.feed(table_str)

    if len(p.tables) != 1:
        logger.warning("Table parser returned more than 1 table, only using first")
    
    # Return list of lists.  There is only 1 table so only the first is returned
    table_output = p.tables[0]

    if query_cfg.get(PROCESS_REMOVE_HEADER_ROW, False):
        table_output = table_output[1:]

    # We need to detect is the key is present, but dict.get() will return 'None' if it's present but undefined.
    if PROCESS_REMOVE_ROWS_IF_EMPTY in query_cfg.keys():
        remove_rows_if_empty = query_cfg.get(PROCESS_REMOVE_ROWS_IF_EMPTY)
        table_output = _remove_rows_if_empty(remove_rows_if_empty, table_output)

    return table_output

def get_table_entry(row, query_cfg):

    return row[query_cfg[COLUMN_NUM]]

# Split an existing table into multiple smaller tables
def get_split_table(table, query_cfg):

    output_tables = []

    if query_cfg.get(PROCESS_SPLIT_TYPE) == "distribute-header-col":
        header_col_num = query_cfg.get("header-col-num", 0)
        for row in table:
            for col_index, col_entry in enumerate(row[(header_col_num+1):]):
                if col_index >= len(output_tables):
                    output_tables.append([])
                output_table_entry = []
                output_table_entry.append(row[header_col_num])
                output_table_entry.append(col_entry)
                output_tables[col_index].append(output_table_entry)

    return output_tables

def get_transposed_table(table, query_cfg):

    return list(map(list, zip(*table)))

def get_remove_table_header_row(table, query_cfg):

    return table[1:]

# The query might constrain whether to return a value or not.  If not, None is returned.
def get_constrained_table_entry(row, query_cfg, current_row_index, current_col_index):
    
    if query_cfg is None:
        query_cfg = {}

    # If the constraint does not exist, then the default values ensure that the conditions are true.
    # If the constraint does exist, then it must be met.
    if query_cfg.get(ROW_NUM, current_row_index) == current_row_index:
           return row[query_cfg.get(COLUMN_NUM, current_col_index)]

    return None

def col_index_defined(query_cfg):

    if query_cfg[COLUMN_NUM] is not None:
        return True
    
    return False

def does_col_index_match(query_cfg, index):

    cfg_index = query_cfg[COLUMN_NUM]
    if cfg_index:
        # There is a value to match
        return cfg_index == index
    
    # There is no value, so no match
    return False

def get_row_entry_by_col_index(row, index):

    return row[index]

def set_table_entry(row, query_cfg, value):

    row[query_cfg[COLUMN_NUM]] = value

    return

# Expecting the xpath to return a list of text nodes,whcih get concatenated
def get_text_section(document, query_cfg):

    paragraphs = document.xpath(query_cfg[XPATH_FIELD])

    output = ""
    for paragraph in paragraphs:
        output += (str(paragraph) + "/n")

    return output

html_dispatch_table = {
    "html-ul":get_document_list_items,
    "html-table":get_document_row_table,
    "html-table-remove-header-row":get_remove_table_header_row,
    "html-table-row":get_table_entry,
    "html-split-table":get_split_table,
    "html-table-transpose":get_transposed_table,
    "html-text":get_document_value,
    "html-text-section":get_text_section
}