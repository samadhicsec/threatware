#!/usr/bin/env python3
"""
Class VerifierIssue
"""

import logging
import utils.load_yaml
import jsonpickle

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader = FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

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

    def getSuccess(self, text_key:str, template_values:dict) -> dict:

        success_text = env.from_string(self.templated_texts.get(text_key)).render(template_values)

        return self._getOutput("Success", success_text, template_values["tm_version"])

    def getError(self, text_key:str, template_values:dict) -> dict:

        error_text = env.from_string(self.templated_texts.get(text_key)).render(template_values)

        return self._getOutput("Error", error_text)

    def tojson(self, output:dict):
        return jsonpickle.encode(output, unpicklable=False)