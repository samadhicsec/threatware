#!/usr/bin/env python3
"""
Class VerifierError
"""

from data.key import key
from enum import Enum
import pprint
from utils import keymaster

class ErrorType(Enum):
    ERROR = 1
    WARNING = 2
    INFO = 3
    NOT_SET = 4

    def __repr__(self):
        return self.name

class VerifierError:

    # This will be set as a class variable so all VerifierError instances use the same config
    error_config = {"default-severity":"ERROR","location-text":"{}", "entry-text":"{}"}

    def __init__(self, verifier_config:dict, verifier:str, description, location:key, errortype:ErrorType = ErrorType.NOT_SET, section:str = None, entry:str = None):

        #error_config = self.error_config["errors"]

        self.verifier = verifier
        self.description = description

        self.errortype = errortype
        if errortype == ErrorType.NOT_SET:
            self.errortype = ErrorType[self.error_config["default-severity"].upper()]

        self.section = None
        # Find the section for the location
        if section is not None:
            self.section = self.error_config["location-text"].format(section)
        if location is not None and self.section is None:
            sectionKey = keymaster.get_section_for_key(location)
            if sectionKey.getProperty("section") is not None:
                # 'section' shoud just be a string
                self.section = self.error_config["location-text"].format(sectionKey.getProperty("section"))

        # Get the row-identifier for the location
        self.entry = None
        if entry is not None:
            self.entry = self.error_config["entry-text"].format(entry)
        if location is not None and entry is None:
            row_identifier_name, row_identifier_value = keymaster.get_row_identifiers_for_key(location)
            self.entry = self.error_config["entry-text"].format(row_identifier_name, row_identifier_value)
            # # Find the entry in the section to help locate the error
            # if location.hasTag("row-identifier") or location.getProperty("rowID") is not None:
            #     # It's possible the entry key is the same as the error location, in which case the 
            #     # "rowID" property will not be set on it (it would be a circular reference)
            #     entryKey = location.getProperty("rowID")
            #     if entryKey is None:
            #         #print(f"Entry is tagged with row-identifier, property 'value' = {location.getProperty('value')}")
            #         name = location.name
            #         self.entry = self.error_config["entry-text"].format(name, location.getProperty("value"))
            #     else:
            #         #print("Entry has property rowID")
            #         name = entryKey.name
            #         self.entry = self.error_config["entry-text"].format(name, entryKey.getProperty("value"))
            
    def _get_state(self):
        output = {}
        output['type'] = self.errortype.name
        output['description'] = self.description
        if self.section is not None:
            output['section'] = self.section
        if self.entry is not None:
            output['entry'] = self.entry
        output["verifier"] = self.verifier
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    def __repr__(self):
        return pprint.pformat(self._get_state(), sort_dicts=False)
