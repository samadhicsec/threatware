#!/usr/bin/env python3

import logging
from lxml import etree
import lxml.html
from lxml.etree import XPathError, XPathEvalError
#from lxml.html.clean import clean_html
from html_table_parser import HTMLTableParser
#from html_table_extractor.extractor import Extractor
from utils import match
from utils.property_str import pstr
from html2text import HTML2Text

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

XPATH_FIELD = "xpath"
ATTR_NAME = "attribute-name"
COLUMN_NUM = "column-num"
ROW_NUM = "row-num"
PROCESS_IGNORE_COLS = "ignore-cols"
PROCESS_REMOVE_HEADER_ROW = 'remove-header-row'
PROCESS_REMOVE_ROWS_IF_EMPTY = "remove-rows-if-empty"
PROCESS_SPLIT_TYPE = "split-type"
HTML2TEXT_OPTIONS = "html2text-options"
HTML2TEXT_ALLOWLIST = [
    "unicode_snob",
    "escape_snob",
    "links_each_paragraph",
    "body_width",
    "skip_internal_links",
    "inline_links",
    "protect_links",
    "google_list_indent",
    "ignore_links",
    "ignore_mailto_links",
    "ignore_images",
    "images_as_html",
    "images_to_alt",
    "images_with_size",
    "ignore_emphasis",
    "bypass_tables",
    "ignore_tables",
    "google_doc",
    "ul_item_mark",
    "emphasis_mark", 
    "strong_mark",
    "single_line_break",
    "use_automatic_links",
    "hide_strikethrough",
    "mark_code",
    "wrap_list_items",
    "wrap_links",
    "wrap_tables",
    "pad_tables",
    "default_image_alt",
    "open_quote", 
    "close_quote", 
    "include_sup_sub"
]

def get_document(document_str, mapping):

    document = lxml.html.document_fromstring(document_str)

    if preprocess := mapping.get("preprocess", None):

        for processor in preprocess:
            selector = processor.get("selector", "//")

            try:
                # Navigate to the <table> element
                selection = document.xpath(selector)
            except XPathError:
                logger.warning(f"Pre-process selector '{selector}' caused an error")
                continue
            
            for ele in selection:
                # Order here matters, do attributes first because that is irresptive of tags or elements
                if attributes_to_strip := processor.get("strip-attributes", None):
                    etree.strip_attributes(ele, attributes_to_strip)
                # Do elements before tags because we may want to strip all tags and so if we did tags first we couldn't strip the elements
                if elements_to_strip := processor.get("strip-elements", None):
                    etree.strip_elements(ele, elements_to_strip)
                if tags_to_strip := processor.get("strip-tags", None):
                    etree.strip_tags(ele, tags_to_strip)
                
                

    # This is a hack.  For reasons unknown XPath queries start failing for no obvious reason
    # once strip_* methods are called.  So we reload the processed XML from a string.  Lame.
    new_doc_bstr = lxml.html.tostring(document, encoding='unicode')
    new_doc_str = new_doc_bstr
    document = lxml.html.document_fromstring(new_doc_str)

    return document


def get_document_section(document, query_cfg):

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return None

    try:
        section_list = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        section_list = []

    if len(section_list) == 0:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned no results")
        return None

    if len(section_list) != 1:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned more than 1 result, only using first")

    return section_list[0]

def get_document_list_items(document, query_cfg):

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return []

    try:
        list_items = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        list_items = []

    logger.debug(f"Query '{query_cfg[XPATH_FIELD]}' return {len(list_items)} elements")

    return list_items

def get_document_value(document, query_cfg) -> str:

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return None

    try:
        value_list = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        value_list = []

    logger.debug(f"Query '{query_cfg[XPATH_FIELD]}' return {len(value_list)} elements")

    if len(value_list) == 0:
        return None
    if len(value_list) > 1:
        logger.warning(f"Retreived {len(value_list)} document values when 1 was expected.  Using first.")
        
    location = ""

    if not isinstance(value_list[0], str):
        logger.warning(f"Expected results 'str', got '{type(value_list[0])}', for query '{query_cfg[XPATH_FIELD]}'")
    else:
        # It's a string, so we can't extract a location from it.  Try to strip away the xpath path that makes the result a string to get to the
        # element that contains the string.
        query = query_cfg[XPATH_FIELD]
        if query.endswith("//text()"):
            query = query[:-8]
        if query.endswith("/text()"):
            query = query[:-7]
        elif "/@" in query:
            query = query[0:query.rfind("/@")]
        
        try:
            value_element = document.xpath(query)
        except (XPathError, XPathEvalError):
            logger.warning(f"XPath query '{query}' caused an error")
            value_list = []
        if len(value_element) == 1:
            if hasattr(value_element[0], "xpath"):
                location = document.getroottree().getpath(value_element[0])
        
    # Despite checking this is a str, it could be a _ElementUnicodeResult, which doesn't serialise to JSON nicely.  So explicitly convert.

    if location:
        return pstr(str(value_list[0]), properties = {"location":location})
    
    logger.info(f"Returning value '{str(value_list[0])}' without location")
    return pstr(str(value_list[0]))

def get_element_text(document, query_cfg) -> str:

    if (element := _get_element(document, query_cfg)) is None:
        return None
    
    text = element.text_content()

    # The output from lxml is usually not a string, so explicitly convert
    return pstr(str(text), properties = {"location": element.getroottree().getpath(element)})


def get_element_attribute(document, query_cfg) -> str:

    if (element := _get_element(document, query_cfg)) is None:
        return None
    
    if not query_key_defined(query_cfg, ATTR_NAME):
        logger.warning(f"'{ATTR_NAME}' not specified in query configuration")

    attribute = element.get(query_cfg[ATTR_NAME], None)

    if attribute is None:
        logger.warning(f"Attribute '{query_cfg[ATTR_NAME]}' not found in element")

    # The output from lxml is usually not a string, so explicitly convert
    return pstr(str(attribute), properties = {"location": element.getroottree().getpath(element)})
    

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

def get_table_xpaths(table_element):
    row_xpaths = []
    roottree = table_element.getroottree()
    rows = table_element.xpath('.//tr')
    
    for row_index, row in enumerate(rows):
        col_xpaths = []
        cells = row.xpath('.//td | .//th')
        for cell_index, cell in enumerate(cells):
            # Since the cell element could be a td or th, we must make sure we get the correct xpath
            #cell_xpath = f"{table_element.getroottree().getpath(table_element)}//tr[{row_index + 1}]//{cell.tag}[{cell_index + 1}]"
            cell_xpath = roottree.getpath(cell)    # This is dangerous though as pre-processing may make the xpath here invalid when applied to the original document
            col_xpaths.append(cell_xpath)
        
        row_xpaths.append(col_xpaths)
    
    return row_xpaths

def get_document_row_table(document, query_cfg):

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return None

    try:
        # Navigate to the <table> element
        table_list = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        table_list = []

    if len(table_list) == 0:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned no results")
        return []
    elif len(table_list) != 1:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' returned more than 1 result, only using first")

    table_ele = table_list[0]

    # Get the XPath to each table element
    table_xpaths = get_table_xpaths(table_ele)

    # For future reference:
    #  'strip_tags' will remove the element tag and attributes but not the content
    #  'strip_elements' will remove everything, tag, attributes and content

    # Parsing a table is much easier if we remove HTML elements that just style the output, and since the output of
    # this method is no longer XML, we know subsequent queries don't rely on these elements.
    # Stripping span doesn't affect content (and Google Docs have A LOT of span elements)
    #etree.strip_tags(table_ele, "span")
    # Reluctantly removing 'superscript' elements.  It seems Google Docs will add single letter superscript to elements
    # when you download the doc as HTML, where that text is hihglight as part of a comment.  Lesser of two evils is to 
    # not support 'superscript' elements (as we have to allow a document with comments to be verified)
    #etree.strip_elements(table_ele, "sup")

    # When we call HTMLTableParser it will strip links i.e. <a> and replace them with data_separator, which is /n, 
    # this causes problems because if the link is in the middle of text it introduces a /n which messes up formatting.
    # We don't want to change data_separator because actual html breaks need to be preserved.  So we just strip links,
    # which is fine because we can't store them anyway and they should affect validation
    #etree.strip_tags(table_ele, "a")

    ## Removing this code as using HTMLTableParser with data_separator='\n' should have the same affecet
    # Stripping attributes of <p> elements doesn't affect content, but we leave them in because they are usually used
    # like newlines, which is what we replace them with further down.
    #for ele in table_ele.findall('.//p'):
    #for ele in table_ele.findall('.'):
    #    etree.strip_attributes(ele, "style")

    # Extract as string
    table_bstr = lxml.html.tostring(table_ele, encoding='unicode')

    ## TODO maybe use lxml.html.clean.clean_html in the future, but need to check how it handles imperfect HTML (I'm looking at you Confluence)
    #table_bstr = clean_html(table_bstr)
    
    ## Removing this code as using HTMLTableParser with data_separator='\n' should have the same affecet
    # HTMLTableParser will strip all tags from table entries, but sometimes that information is relevant e.g. <p></p> as newlines
    # This doesn't always work.  The '\n' need to be adjacent to actual text.  If the p-tags surround a <a> for instance then the '\n' is removed by HTMLTableParser
    #table_str = table_bstr.replace("</p><p>", "<a>\n</a>")
    #table_str = table_bstr.replace("</p><p>", "</p>\n<p>")
    table_str = table_bstr

    # Would like to use this libary, but it doesn't support changing the separator character.
    # extractor = Extractor(table_str)
    # extractor.parse()
    # table_output = extractor.return_list()

    # Non-breaking spaces cause string matching issues (usually from cut & paste from somewhere else).  So let's replace those with normal spaces.
    table_str = table_str.replace("\xa0", " ")

    # Parse as table
    # Tags in cells are stripped and the tags text content is joined using data_separator
    # HTMLTableParser defaults to decode_html_entities=False, but we want to keep those characters e.g. &
    p = HTMLTableParser(data_separator='\n', decode_html_entities=True)
    #p = HTMLTableParser(data_separator=' ')

    p.feed(table_str)

    if len(p.tables) != 1:
        logger.warning("Table parser returned more than 1 table, only using first")
    
    # Return list of lists.  There is only 1 table so only the first is returned
    table_output = p.tables[0]

    # Combine the XPath to each table cell wit the value in each table cell
    table_values = table_output
    if len(table_values) != len(table_xpaths):
        # We'll cope with this by using empty XPath vlaues
        logger.warning(f"Table values '{len(table_values)}' did not match the table xpaths '{len(table_xpaths)}'")
    for row_index, row in enumerate(table_values):
        if row_index >= len(table_xpaths):
            # Make entire row empty XPath values
            logger.warning(f"Table value row '{row_index}' did not have a corresponding table xpath")
            row_xpath = [""]*len(row)
        else:
            row_xpath = table_xpaths[row_index]
        for col_index, value in enumerate(row):
            if col_index >= len(row_xpath):
                # Make column XPath entry empty.  Remember, this row could contain real XPath values, just not enough of them
                logger.warning(f"Table value '{value}' did not have a corresponding table xpath")
                col_xpath = ""
            else:
                col_xpath = row_xpath[col_index]
            
            #table_output[row_index][col_index] = {"location":col_xpath, "value":value}
            table_output[row_index][col_index] = pstr(value, properties={"location":col_xpath})

    if query_cfg.get(PROCESS_REMOVE_HEADER_ROW, False):
        table_output = table_output[1:]

    # We need to detect is the key is present, but dict.get() will return 'None' if it's present but undefined.
    if PROCESS_REMOVE_ROWS_IF_EMPTY in query_cfg.keys():
        remove_rows_if_empty = query_cfg.get(PROCESS_REMOVE_ROWS_IF_EMPTY)
        table_output = _remove_rows_if_empty(remove_rows_if_empty, table_output)

    return table_output

def get_table_entry(row, query_cfg):

    if not query_key_defined(query_cfg, COLUMN_NUM):
        return None

    if query_cfg[COLUMN_NUM] >= len(row):
        logger.warning(f"Query configuration '{COLUMN_NUM}' with value '{query_cfg[COLUMN_NUM]}' was larger than the '{len(row)}' available columns (using zero-based indexing)")
        return None
    
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

def query_key_defined(query_cfg, query_cfg_key, optional = False):

    if query_cfg is None:
        logger.warning(f"Query configuration is not specified")
        return False

    if not isinstance(query_cfg, dict):
        logger.warning(f"Query configuration is not a set of key/value pairs")
        return False

    if query_cfg_key not in query_cfg:
        if not optional:
            logger.warning(f"Query configuration '{query_cfg_key}' was not present in '{query_cfg}'")
        return False
    
    return True

def _get_element(document, query_cfg) -> str:

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return None

    try:
        value_list = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        value_list = []

    logger.debug(f"Query '{query_cfg[XPATH_FIELD]}' return {len(value_list)} elements")

    if len(value_list) == 0:
        return None
    if len(value_list) > 1:
        logger.warning(f"Retreived {len(value_list)} document values when 1 was expected.  Using first.")

    return value_list[0]

def does_col_index_match(query_cfg, index):

    if not query_key_defined(query_cfg, COLUMN_NUM):
        return False

    cfg_index = query_cfg[COLUMN_NUM]
    if cfg_index:
        # There is a value to match
        return cfg_index == index
    
    # There is no value, so no match
    return False

def get_row_entry_by_col_index(row, index):

    if index >= len(row):
        logger.warning(f"Index value '{index}' was larger than the '{len(row)}' available rows (using zero-based indexing)")
        return None

    return row[index]

def set_table_entry(row, query_cfg, value):

    if not query_key_defined(query_cfg, COLUMN_NUM):
        return

    row[query_cfg[COLUMN_NUM]] = value

    return

# Expecting the xpath to return a list of nodes, which get text exrtacted and concatenated
def get_text_section(document, query_cfg):

    if not query_key_defined(query_cfg, XPATH_FIELD):
        return None

    try: 
        nodes = document.xpath(query_cfg[XPATH_FIELD])
    except XPathError:
        logger.warning(f"XPath query '{query_cfg[XPATH_FIELD]}' caused an error")
        nodes = []

    input = ""
    for node in nodes:
        input += lxml.html.tostring(node, encoding='unicode')

    h2t = HTML2Text()
    if query_key_defined(query_cfg, HTML2TEXT_OPTIONS, optional=True) and isinstance(query_cfg[HTML2TEXT_OPTIONS], dict):
        for option, value in query_cfg[HTML2TEXT_OPTIONS].items():
            if option in HTML2TEXT_ALLOWLIST:
                setattr(h2t, option, value)
            else:
                logger.warning(f"html2text option '{option}' not in allowed list")
    
    output = h2t.handle(str(input))

    return pstr(output, properties={"location":query_cfg[XPATH_FIELD]})

html_dispatch_table = {
    "html-ul":get_document_list_items,
    "html-table":get_document_row_table,
    "html-table-remove-header-row":get_remove_table_header_row,
    "html-table-row":get_table_entry,
    "html-split-table":get_split_table,
    "html-table-transpose":get_transposed_table,
    "html-text":get_document_value,
    "html-element-text":get_element_text,
    "html-element-attribute": get_element_attribute,
    "html-text-section":get_text_section
}