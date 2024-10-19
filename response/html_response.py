import logging
import jsonpickle, json
from typing import List
from lxml import etree
import lxml.html
from lxml.etree import XPathError
from utils.request import Request
from response.response_config import HTMLConfig, SchemeSpecificConfig, FindingsConfig, BannerConfig, HTMLInject
from utils.output import FormatOutput
from language.translate import Translate

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

THREATWARE_RESULT_ERRORS = "errors"
THREATWARE_RESULT_NO_ERRORS = "no-errors"

def _inject_into_HTML(document, config:HTMLInject):

    try:
        elements = document.xpath(config.location_element)
    except XPathError:
        logger.warning(f"XPath query '{config.location_element}' caused an error")
        
    if len(elements) == 0:
        logger.warning(f"XPath query '{config.location_element}' returned no elements")
        return
    if len(elements) > 1:
        logger.warning(f"XPath query '{config.location_element}' returned multiple elements, using first")
        
    element = elements[0]

    element_index = config.location_index

    element_list = []

    # Create the script includes
    for script in config.include_scripts:
        element_list.append(etree.Element("script", src=script))

    # Create the style includes
    for style in config.include_stylesheets:
        element_list.append(etree.Element("link", rel="stylesheet", href=style))
    
    # Create the inline element
    if config.inline_element:
        ele = etree.fromstring(config.inline_element)
        element_list.append(ele)                 

    # Create the inline style
    if config.inline_style:
        ele = etree.Element("style", type="text/css")
        ele.text = config.inline_style
        element_list.append(ele)

    # Create the inline script
    if config.inline_script:
        ele = etree.Element("script")
        ele.text = config.inline_script
        element_list.append(ele)

    # Insert the elements into the document
    if -1 == element_index:
        for sub_element in element_list:
            element.append(sub_element)
    else:
        for i, sub_element in enumerate(element_list):
            element.insert(element_index + i, sub_element)

def _inject_scheme_specfic_into_HTML(document, scheme_specific_config:List[SchemeSpecificConfig], scheme:str):

    for scheme_config in scheme_specific_config:
        if scheme_config.matches(scheme):
            _inject_into_HTML(document, scheme_config.htmlinject)


def _inject_banner_into_HTML(document, banner_config:BannerConfig, issues, showing_all_errors:bool, result:FormatOutput, template_values:dict):

    banner_msg = result.getDescription()
    threatware_result = THREATWARE_RESULT_NO_ERRORS
    if len(issues) > 0:
        threatware_result = THREATWARE_RESULT_ERRORS
        if not showing_all_errors:
            banner_msg = f"{banner_msg}{Translate.localise(template_values, banner_config.missingfindingstextkey)}"
            
    # Inject the banner to inform the user of the state of the action
    _inject_into_HTML(document, banner_config.htmlinject)

    # Inject the text we want to display.  Since we inject at position zero, this will run before the above banner config
    _inject_into_HTML(document, HTMLInject({
        "location": {
            "element": "//html/body", 
            "index": 0
        }, 
        "inline": {
            "script": f"""
                var banner_msg = \"{banner_msg}\";
                var threatware_result = \"{threatware_result}\";
            """
        }
    }))

def _inject_findings_into_HTML(document, issues:dict, findings_config:FindingsConfig, template_values:dict):
    """
    Injects the findings into the HTML document
    """
    showing_all_errors = True

    # Add attributes to the elements the findings are associated with
    finding_id_count = -1
    for issue in issues:
        try:
            finding_id_count += 1
            xpath = issue.issue_key.properties.get("location", "")
            if xpath == "":
                showing_all_errors = False
                continue
            element = document.xpath(xpath)[0]
            if findings_config.finding_attribute in element.attrib:
                element.attrib[findings_config.finding_attribute] = f"{element.attrib[findings_config.finding_attribute]} {finding_id_count}"
            else:
                element.attrib[findings_config.finding_attribute] = f"{finding_id_count}"

            if issue.errortype.name == "ERROR":
                element.attrib[findings_config.finding_type] = "error"
            elif issue.errortype.name == "WARNING" and findings_config.finding_type not in element.attrib:
                element.attrib[findings_config.finding_type] = "warning"
            elif issue.errortype.name == "INFO" and findings_config.finding_type not in element.attrib:
                element.attrib[findings_config.finding_type] = "info"

            if findings_config.finding_class in element.attrib:
                element.attrib[findings_config.finding_class] = f"{element.attrib[findings_config.finding_class]} {issue.verifier}"
            else:
                element.attrib[findings_config.finding_class] = f"{issue.verifier}"

        except XPathError:
            logging.warning(f"Could not find location {xpath} in the document")
        except IndexError:
            logging.warning(f"Could not find location {xpath} in the document")

    # Inject the findings into the document
    json_issues = jsonpickle.encode(issues, unpicklable=False)

    _inject_into_HTML(document, HTMLInject({
        "location": {
            "element": "//html/body", 
            "index": -1
        }, 
        "inline": {
            "script": f"""
                const threatwarefindings = {json_issues};
                const threatwareRequest = {json.dumps(Request.get())};
            """
        }
    }))

    # Inject the ability to display the findings
    _inject_into_HTML(document, findings_config.htmlinject)

    return showing_all_errors

def get_html_response(config:HTMLConfig, result:FormatOutput, html_doc:str, template_values:dict):

    #content = result.getDetails()
    #if "issues" not in content:
    #    logging.error(f"Expecting 'issues' key in content but none was found")
    issues = result.getDetails().getIssues()

    document = lxml.html.document_fromstring(html_doc)

    # Add any scheme specific content to make the exported HTML look like the original
    _inject_scheme_specfic_into_HTML(document, config.schemeSpecificConfig, Request.scheme)

    # Add the findings to the HTML document, and the ability to show the findings to the user
    showing_all_errors = _inject_findings_into_HTML(document, issues, config.findingsConfig, template_values)

    # Add a banner to the top of the body saying whether the validation passed, failed,or failed and not all errors are shown
    _inject_banner_into_HTML(document, config.bannerConfig, issues, showing_all_errors, result, template_values)

    new_html_bstr = lxml.html.tostring(document, encoding='unicode')
    new_html_str = new_html_bstr    # Required hack to get around the fact that the lxml.html.tostring() function returns a byte string, not a string

    # Add "<!doctype html>" to the top of the page.  This tells the brwoser to use standards mode.  This is important as the browser will use quirks mode if this is not present.
    new_html_str = "<!doctype html>\n" + new_html_str
    
    return new_html_str

