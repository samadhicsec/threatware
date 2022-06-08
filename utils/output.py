#!/usr/bin/env python3
"""
Class FormatOutput
"""

import logging
from enum import Enum
from pathlib import Path
from utils.config import ConfigBase
from utils import load_yaml
from utils.config import ConfigBase
from language.translate import Translate
import jsonpickle

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# from jinja2 import Environment, FileSystemLoader, select_autoescape
# env = Environment(
#     loader = FileSystemLoader(searchpath="./"),
#     autoescape=select_autoescape()
# )

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
    output_format:str = "json"
    #translator:Translate

    def __init__(self, output_config:dict):

        #formatoutput_texts = self.translator.localiseYamlFile(OUTPUT_TEXTS_YAML_PATH).get("output-texts")
        formatoutput_texts = load_yaml.yaml_file_to_dict(ConfigBase.getConfigPath(OUTPUT_TEXTS_YAML_PATH)).get("output-texts")
        # self.information = env.from_string(formatoutput_texts.get("information")).render(self.translator.translations)
        # self.success = env.from_string(formatoutput_texts.get("success")).render(self.translator.translations)
        # self.error = env.from_string(formatoutput_texts.get("error")).render(self.translator.translations)
        self.information = Translate.localise(formatoutput_texts, "information")
        self.success = Translate.localise(formatoutput_texts, "success")
        self.error = Translate.localise(formatoutput_texts, "error")
        
        self.templated_texts:dict = load_yaml.yaml_file_to_dict(ConfigBase.getConfigPath(output_config.get("template-text-file"))).get("output-texts")
        # Need to merge these dicts at each localisation entry
        for dict_key in formatoutput_texts.keys():
            if dict_key in self.templated_texts:
                self.templated_texts[dict_key] = formatoutput_texts[dict_key] | self.templated_texts[dict_key]
            else:
                self.templated_texts[dict_key] = formatoutput_texts[dict_key]
        
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
            output["request"] = FormatOutput.request_parameters["request"]

        return output

    def setInformation(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Information output message """

        if template_values is None:
            template_values = {}
            
        self.type = OutputType.INFO
        self.description = Translate.localise(self.templated_texts, text_key, template_values | self.request_parameters)
        #self.description = env.from_string(self.templated_texts.get(text_key, f"Could not find text for key {text_key}")).render(template_values | self.request_parameters | self.translator.translations)
        self.details = details
        
        return

    def setSuccess(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Success output message """

        if template_values is None:
            template_values = {}

        self.type = OutputType.SUCCESS
        self.description = Translate.localise(self.templated_texts, text_key, template_values | self.request_parameters)
        #self.description = env.from_string(self.templated_texts.get(text_key, f"Could not find text for key {text_key}")).render(template_values | self.request_parameters | self.translator.translations)
        self.details = details

        return

    def setError(self, text_key:str, template_values:dict, details = None):
        """ Returns a localised Error output message """

        if template_values is None:
            template_values = {}

        self.type = OutputType.ERROR
        self.description = Translate.localise(self.templated_texts, text_key, template_values | self.request_parameters)
        #self.description = env.from_string(self.templated_texts.get(text_key, f"Could not find text for key {text_key}")).render(template_values | self.request_parameters | self.translator.translations)
        self.details = details

        return

    def getResult(self) -> OutputType:
        """ Returns an OutputType enum """
        return self.type

    def getDescription(self):
        """ Returns the description """
        return self.description

    def getDetails(self):
        """ Returns the details added to an Info/Success/Error message """
        return self.details

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    def tojson(self):
        return jsonpickle.encode(self, unpicklable=False)

    def toyaml(self):
        return load_yaml.class_to_yaml_str(self._get_state())

    def getContent(self, config_fn = None):

        if config_fn is not None:
            config_fn()

        if FormatOutput.output_format == "yaml":
            return ("text/yaml", self.toyaml())

        return ("application/json", self.tojson())