#!/usr/bin/env python3
"""
Class Response
"""

import logging
from threatware.utils.config import ConfigBase
from threatware.utils.output import FormatOutput
from threatware.utils.load_yaml import yaml_file_to_dict
from threatware.data.key import key as Key
from threatware.utils.request import Request
from threatware.response.response_config import ResponseConfig
from threatware.response.html_response import get_html_response

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

#OUTPUT_TEXTS_YAML = "output_texts.yaml"
#OUTPUT_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(OUTPUT_TEXTS_YAML))

class Response:

    html_document:str = ""

    def __init__(self, output:FormatOutput, meta_override:str = None, force_api_format:bool = False):

        self.response_config = ResponseConfig()
        self.templated_texts = yaml_file_to_dict(ConfigBase.getConfigPath(self.response_config.template_text_file)).get("output-texts")

        if Request.format is None:
            self.format = self._get_default_or_action_override(self.response_config, "format")
        else:
            self.format = Request.format
        if self.format is None:
            self.format = "json"    # Let's default to json if nothing specified
        if force_api_format:
            # We likely have an error situation and don't want to try and return html
            if self.format != "json" or self.format != "yaml":
                self.format = "json"

        self.output = output
        self.meta_override = meta_override

    def getFormat(self):
        return self.format

    def _get_default_or_action_override(self, config:dict, key:str):

        value = config.get(key, {}).get("default", None)
        if not value:
            return None
        
        if isinstance(value, str):
            # Check if there is an action specific override
            if (override := config.get(key, {}).get(Request.action, None)) is not None:
                return override
            return value
        elif isinstance(value, list):
            value.append(config.get(key, []))
            return list(set(value))
        elif isinstance(value, dict):
            override = config.get(key, {})
            return value | override
        else:
            logger.error(f"The response config for key '{key}' is of an unsupported type")
            
        return None
    
    def getContentType(self):

        if self.format == "yaml":
            return "text/yaml"
        if self.format == "html":
            return "text/html"
        
        return "application/json"

    def getHeaders(self):
    
        headers = self._get_default_or_action_override(self.response_config.get("http", {}), "headers")
        if headers is None:
            headers = {}
        headers = headers | { "Content-Type": self.getContentType() }
        
        return headers

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