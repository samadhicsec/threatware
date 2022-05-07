#!/usr/bin/env python3
"""
Class ManageOutput
"""

import logging
import utils.load_yaml
from language.translate import Translate
import jsonpickle

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# from jinja2 import Environment, FileSystemLoader, select_autoescape
# env = Environment(
#     loader = FileSystemLoader(searchpath="./"),
#     autoescape=select_autoescape()
# )

class ManageOutput:

    def __init__(self, config):

        template_text_file = config.get("template-text-file")

        self.templated_texts = utils.load_yaml.yaml_file_to_dict(template_text_file).get("output-texts")

    def _getOutput(self, result, description, details = None):

        output = {}
        output["result"] = result
        output["description"] = description
        if details is not None:
            output["details"] = details

        return output

    def setInformation(self, text_key:str, template_values:dict, details = None) -> dict:

        info_text = Translate.localise(self.templated_texts, text_key, template_values)

        return self._getOutput("Information", info_text, details)

    def setSuccess(self, text_key:str, template_values:dict) -> dict:

        success_text = Translate.localise(self.templated_texts, text_key, template_values)

        return self._getOutput("Success", success_text, template_values["tm_version"])

    def setError(self, text_key:str, template_values:dict) -> dict:

        error_text = Translate.localise(self.templated_texts, text_key, template_values)

        return self._getOutput("Error", error_text)

    def tojson(self, output:dict):
        return jsonpickle.encode(output, unpicklable=False)