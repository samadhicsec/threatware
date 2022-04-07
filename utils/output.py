#!/usr/bin/env python3
"""
Class FormatOutput
"""

import logging
from enum import Enum
from pathlib import Path
from utils import load_yaml
from language.translate import Translate
import jsonpickle

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader = FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

OUTPUT_TEXTS_YAML = "output_texts.yaml"
OUTPUT_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(OUTPUT_TEXTS_YAML))

class OutputType(Enum):
    ERROR = 0
    INFO = 1
    SUCCESS = 2
    NOT_SET = -1

    def __repr__(self):
        return self.name

class FormatOutput:

    request_parameters:dict

    def __init__(self, output_config:dict):

        translate = Translate()
        formatoutput_texts = translate.localiseYamlFile(OUTPUT_TEXTS_YAML_PATH).get("output-texts")
        self.information = env.from_string(formatoutput_texts.get("information")).render()
        self.success = env.from_string(formatoutput_texts.get("success")).render()
        self.error = env.from_string(formatoutput_texts.get("error")).render()
        self.templated_texts = load_yaml.yaml_file_to_dict(output_config.get("template-text-file")).get("output-texts")
        
        self.type = OutputType.NOT_SET
        self.description = None
        self.details = None

    def _get_state(self):

        output = {}
        if self.type == OutputType.ERROR:
            output["result"] = self.error
        elif self.type == OutputType.INFO:
            output["result"] = self.information
        elif self.type == OutputType.SUCCESS:
            output["result"] = self.success

        if self.description is not None:
            output["description"] = self.description
        if self.details is not None:
            output["details"] = self.details
        if FormatOutput.request_parameters is not None:
            output["request"] = FormatOutput.request_parameters

        return output

    def setInformation(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Information output message """

        self.type = OutputType.INFO
        self.description = env.from_string(self.templated_texts.get(text_key)).render(template_values | self.request_parameters)
        self.details = details
        
        return

    def setSuccess(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Success output message """

        self.type = OutputType.SUCCESS
        self.description = env.from_string(self.templated_texts.get(text_key)).render(template_values | self.request_parameters)
        self.details = details

        return

    def setError(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Error output message """

        self.type = OutputType.ERROR
        self.description = env.from_string(self.templated_texts.get(text_key)).render(template_values | self.request_parameters)
        self.details = details

        return

    def getResult(self) -> OutputType:
        """ Returns an OutputType enum """
        return self.type

    def getDetails(self):
        """ Returns the details added to an Info/Success/Error message """
        return self.details

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    def tojson(self):
        return jsonpickle.encode(self, unpicklable=False)