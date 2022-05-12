#!/usr/bin/env python3
"""
Class VerifierIssue
"""

import logging
from enum import Enum
from utils.load_yaml import yaml_register_class
from language.translate import Translate
from utils import keymaster
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# from jinja2 import Environment, FileSystemLoader, select_autoescape
# env = Environment(
#     loader = FileSystemLoader(searchpath="./"),
#     autoescape=select_autoescape()
# )

class ErrorType(Enum):
    ERROR = 1
    WARNING = 2
    INFO = 3
    NOT_SET = 4

    def __repr__(self):
        return self.name

class VerifierIssue:
    """
    Will output an issue with following format:
        type: ERROR
        table: The table where the issue exists
        table-row: The entry name and value where the issue exists
        error-description: A description of the error
        error-data: Any data related to the error
        fix-description: A description of a possible fix
        fix-data: Any data related to the fix
        verifier: The name of the verifier that detected the issue
    """

    # This will be set as a class variable so all Verifier instances use the same config
    issue_config = {"default-severity":"ERROR"}
    templated_error_texts = {}  # Will be read from file

    known_error_keys = [
        "issue_key",
        "issue_value",
        "issue_table",
        "errordata",
        "fixdata"
    ]

    def __init__(self, error_text_key:str, fix_text_key:str, issue_dict:dict, errortype:ErrorType = ErrorType.NOT_SET):

        yaml_register_class(VerifierIssue)

        # given an 'issue_key' we want to construct a context so jinja can use e.g. {{ issuerow['component'].colname }} and {{ issuerow['component'].value }} to get, for instance, the information regarding the 'component' entry for a row.  Might not be that helpful for rows where some entries are multiple values, like for T&C 'components'


        self.verifier = ""  # Gets set externally
        self.errortype = errortype
        if errortype == ErrorType.NOT_SET:
            self.errortype = ErrorType[self.issue_config["default-severity"].upper()]

        if "issue_key" not in issue_dict:
            logger.error("The 'issue_dict' dict must include an 'issue_key' key with a Key object as it's value")
            self.error_desc = f"There was an problem generating the VerifierIssue"
            return

        context = {}

        # Loop through all the values of issue_dict, and any that are Key objects, create a row entry
        for keyentry, valueentry in issue_dict.items():
            if isinstance(valueentry, Key):
                context[keyentry] = {}
                context[keyentry]["name"] = valueentry.name
                context[keyentry]["colname"] = valueentry.getProperty("colname")
                if context[keyentry]["colname"] is None:
                    context[keyentry]["colname"] = context[keyentry]["name"]
                context[keyentry]["value"] = issue_dict.get(keyentry.replace("_key", "_value"), None)
                if sectionKey := keymaster.get_section_for_key(valueentry):
                    context[keyentry]["table"] = sectionKey.getProperty("section")

                rowIDkey = keymaster.get_row_identifier_for_key(valueentry)
                if rowIDkey is not None:
                    row = rowIDkey.getProperty("row")
                    if row is not None:
                        rowentry = {}
                        for rowkeyentry, rowvalueentry in row.items():
                            rowentry[rowkeyentry.name] = {}
                            rowentry[rowkeyentry.name]["colname"] = rowkeyentry.getProperty("colname")
                            rowentry[rowkeyentry.name]["value"] = rowvalueentry
                            if sectionKey := keymaster.get_section_for_key(rowkeyentry):
                                rowentry[rowkeyentry.name]["table"] = sectionKey.getProperty("section")
                        context[keyentry]["row"] = rowentry
                    rowIDentry = {}
                    rowIDentry["name"] = rowIDkey.name
                    rowIDentry["colname"] = rowIDkey.getProperty("colname")
                    if rowIDentry["colname"] is None:
                        rowIDentry["colname"] = rowIDentry["name"]
                    rowIDentry["value"] = rowIDkey.getProperty("value")
                    if sectionKey := keymaster.get_section_for_key(rowIDkey):
                        rowIDentry["table"] = sectionKey.getProperty("section")
                    context[keyentry]["rowID"] = rowIDentry
                else:
                    # A 2 column table has no rowID
                    context[keyentry]["rowID"] = context[keyentry]
                    context[keyentry]["row"] = context[keyentry]
            else:
                context[keyentry] = valueentry

        #context["translate"] = self.templated_translations["translate"]

        #for known_key in self.known_error_keys:
        #    setattr(self, known_key, issue_dict.get(known_key, None))
        
        # Does the error_text_key exist? It is mandatory
        # if (error_text := self.templated_error_texts.get(error_text_key, None)) is None:
        #     self.error_desc = f"Could not find error text for '{error_text_key}'"
        #     return

        # We support the caller setting the issue table to any value they want, but if not set we populate it
        if context["issue_key"] is not None and context.get("issue_table") is None:
            sectionKey = keymaster.get_section_for_key(issue_dict["issue_key"])
            context["issue_table"] = sectionKey.getProperty("section")
        
        ### 'context' is set, so below here don't change it, just use it to render text ###
        
        # TODO gracefully handle templating exceptions from jinja, notably when it can't find the value when rendering

        # Set the issue table text
        self.issue_table_text = Translate.localise(self.templated_error_texts, "location-text", context)
        
        # We support the caller disabling the display of the issue table row information
        if "issue_table_row" in issue_dict and issue_dict.get("issue_table_row") is None:
            self.issue_table_row_text = None
        else:
            self.issue_table_row_text = Translate.localise(self.templated_error_texts, "entry-text", context)
        
        # Set the error description
        #self.error_desc = env.from_string(error_text).render(context)
        self.error_desc = Translate.localise(self.templated_error_texts, error_text_key, context)
        self.errordata = issue_dict.get("errordata")
        
        # Set any fix text specified
        #if fix_text_key is not None and self.templated_error_texts.get(fix_text_key, None) is not None:
        if fix_text_key is not None:
            self.fix_desc = Translate.localise(self.templated_error_texts, fix_text_key, context)
        self.fixdata = issue_dict.get("fixdata")

    def isError(self):
        return self.errortype == ErrorType.ERROR

    def isWarning(self):
        return self.errortype == ErrorType.WARNING

    def isInfo(self):
        return self.errortype == ErrorType.INFO

    def _get_state(self):

        # TODO - it would be good to substitute dict key names using the verifier_values.yaml file.  Probably need to recurse on things like fix-data

        output = {}
        output['type'] = self.errortype.name
        
        if getattr(self, "issue_table_text", None) is not None:
            output['table'] = self.issue_table_text
        if getattr(self, "issue_table_row_text", None) is not None:
            output['table-row'] = self.issue_table_row_text
        
        output['error-description'] = getattr(self, "error_desc", "")
        if getattr(self, "errordata", None) is not None:
            output['error-data'] = self.errordata

        if getattr(self, "fix_desc", None) is not None:
            output['fix-description'] = self.fix_desc
        if getattr(self, "fixdata", None) is not None:
            output['fix-data'] = self.fixdata

        output["verifier"] = getattr(self, "verifier", "")
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())

# class VerifierError:

#     # This will be set as a class variable so all VerifierError instances use the same config
#     error_config = {"default-severity":"ERROR","location-text":"{}", "entry-text":"{}"}
#     values = {}
#     templated_error_texts = {}

#     def __init__(self, verifier_config:dict, verifier:str, description, location:key, errortype:ErrorType = ErrorType.NOT_SET, section:str = None, entry:str = None):

#         # TODO - Separate error text and any other output or value text into it's own file, so it can easily be changed.  Other config files when they need to use these values can reference the field name.  Sometimes the field name should be configurable e.g. in_scope_id: YES_TEXT, YES_TEXT:"Yes"
#         # TODO - include an "allowed_values" parameter, for more clearly showing what is allowed.
#         # TODO - introduce a template language (jinja) for the error texts, and pass in an object with the values (include verifier, location as well), combining them in this method.

#         #error_config = self.error_config["errors"]

#         self.verifier = verifier
#         self.description = description

#         self.errortype = errortype
#         if errortype == ErrorType.NOT_SET:
#             self.errortype = ErrorType[self.error_config["default-severity"].upper()]

#         self.section = None
#         # Find the section for the location
#         if section is not None:
#             self.section = self.error_config["location-text"].format(section)
#         if location is not None and self.section is None:
#             sectionKey = keymaster.get_section_for_key(location)
#             if sectionKey.getProperty("section") is not None:
#                 # 'section' shoud just be a string
#                 self.section = self.error_config["location-text"].format(sectionKey.getProperty("section"))

#         # Get the row-identifier for the location
#         self.entry = None
#         if entry is not None:
#             self.entry = self.error_config["entry-text"].format(entry)
#         if location is not None and entry is None:
#             row_identifier_name, row_identifier_value = keymaster.get_row_identifiers_for_key(location)
#             self.entry = self.error_config["entry-text"].format(row_identifier_name, row_identifier_value)
#             # # Find the entry in the section to help locate the error
#             # if location.hasTag("row-identifier") or location.getProperty("rowID") is not None:
#             #     # It's possible the entry key is the same as the error location, in which case the 
#             #     # "rowID" property will not be set on it (it would be a circular reference)
#             #     entryKey = location.getProperty("rowID")
#             #     if entryKey is None:
#             #         #print(f"Entry is tagged with row-identifier, property 'value' = {location.getProperty('value')}")
#             #         name = location.name
#             #         self.entry = self.error_config["entry-text"].format(name, location.getProperty("value"))
#             #     else:
#             #         #print("Entry has property rowID")
#             #         name = entryKey.name
#             #         self.entry = self.error_config["entry-text"].format(name, entryKey.getProperty("value"))
            
#     def _get_state(self):
#         output = {}
#         output['type'] = self.errortype.name
#         output['description'] = self.description
#         if self.section is not None:
#             output['section'] = self.section
#         if self.entry is not None:
#             output['entry'] = self.entry
#         output["verifier"] = self.verifier
#         return output

#     def __getstate__(self):
#         """ Used by jsonpickle to state of class to output """
#         return self._get_state()

#     def __repr__(self):
#         return pprint.pformat(self._get_state(), sort_dicts=False)
