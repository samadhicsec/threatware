#!/usr/bin/env python3
"""
Class Response
"""

import logging
from utils.config import ConfigBase
from utils.output import FormatOutput
from utils.load_yaml import yaml_file_to_dict
from data.key import key as Key
from language.translate import Translate
from utils.request import Request
from response.response_config import ResponseConfig
from response.html_response import get_html_response

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

#OUTPUT_TEXTS_YAML = "output_texts.yaml"
#OUTPUT_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(OUTPUT_TEXTS_YAML))

class Response:

    html_document:str = ""

    def __init__(self, output:FormatOutput, meta_override:str = None, force_api_format:bool = False):

        self.format = Request.format
        if force_api_format:
            # We likely have an error situation and don't want to try and return html
            if self.format != "json" or self.format != "yaml":
                self.format = "json"
        self.output = output
        self.meta_override = meta_override

        self.response_config = ResponseConfig()
        self.templated_texts = yaml_file_to_dict(ConfigBase.getConfigPath(self.response_config.template_text_file)).get("output-texts")

    
    def getContentType(self):

        if self.format == "yaml":
            return "text/yaml"
        if self.format == "html":
            return "text/html"
        
        return "application/json"

    def getBody(self):

        if self.meta_override is not None:
            Key.config_serialisation(self.meta_override)

        if self.format == "yaml":
            return self.output.toyaml()
        if self.format == "html":
            return get_html_response(self.response_config.htmlConfig, self.output, self.html_document, self.templated_texts)
        
        return self.output.tojson()

    @classmethod
    def setDocument(cls, document):

        cls.html_document = document