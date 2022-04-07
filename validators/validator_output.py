#!/usr/bin/env python3
"""
Class ValidatorOutput
"""
import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader = FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

class ValidatorOutput:
    """
    Holds the output of a validator and is used to format output of validator
    """

    templated_translations = {}    # Will be read from file
    templated_output_texts = {}
    validator_config = {}

    def __init__(self, validator_tag:str = None, validating_key = None, validating_value = None):
        """
        Create a ValidatorOutput object

        Parameters
        ----------
        validator_tag : str
            The tag that will be looked up in the validator config YAML to get the validator method and config to use
        validating_key : 
            The key of the entry being validated
        validating_value : 
            The value of the entry being validated
        """

        self.validator_tag = validator_tag
        self.validating_key = validating_key
        self.validating_value = validating_value
        self.validator_name = None
        self.validator_module = None
        self.result = False
        self.description = None
        self.error = None


    def _get_state(self):

        output = {}
        output['validator'] = self.validator_tag
        if not self.error:
            output['validates'] = self.result
            validator_output_texts = self.templated_output_texts.get(self.validator_tag, {}).get("text", {})
            if self.result:
                templ_desc = validator_output_texts.get("output_text_valid")
            else:
                templ_desc = validator_output_texts.get("output_text_invalid")

            context = {}
            context["translate"] = self.templated_translations["translate"]
            context["key"] = {}
            context["key"]["name"] = self.validating_key.name
            context["key"]["colname"] = self.validating_key.getProperty("colname")
            context["key"]["value"] = self.validating_value
            context["config"] = ValidatorOutput.validator_config.get(self.validator_tag, {}).get("config")
            
            output['description'] = env.from_string(templ_desc).render(context)
        else:
            output["error"] = self.error
        
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()