#!/usr/bin/env python3
"""
Class ValidatorOutput
"""

from language.translate import Translate

import logging
from utils.load_yaml import yaml_register_class

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


class ValidatorOutput:
    """
    Holds the output of a validator and is used to format output of validator
    """

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

        yaml_register_class(ValidatorOutput)

        self.validator_tag = validator_tag
        self.validating_key = validating_key
        self.validating_value = validating_value
        self.validator_name = None
        self.validator_module = None
        self.validator_result = False
        self.error = None

    def tag(self):
        return self.validator_tag
    
    def result(self):
        return self.validator_result
    
    def details(self):
        if not self.error:    
            context = {}
            context["key"] = {}
            context["key"]["name"] = self.validating_key.name
            context["key"]["colname"] = self.validating_key.getProperty("colname")
            context["key"]["value"] = self.validating_value
            context["config"] = ValidatorOutput.validator_config.get(self.validator_tag, {}).get("config")

            validator_output_texts = self.templated_output_texts.get(self.validator_tag, {}).get("text", {})
            if self.validator_result:
                return Translate.localise(validator_output_texts, "output_text_valid", context)
            else:
                return Translate.localise(validator_output_texts, "output_text_invalid", context)
        else:
            return self.error
        
    def _get_state(self):

        output = {}
        output['validator'] = self.tag()
        if not self.error:
            output['validates'] = self.result()
            output['description'] = self.details()
        else:
            output["error"] = self.error
        
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())