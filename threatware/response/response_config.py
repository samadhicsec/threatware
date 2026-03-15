#!/usr/bin/env python3
"""
Loads output format confgiuration
"""

import logging
from pathlib import Path
from threatware.data import value
from threatware.utils.config import ConfigBase
import re
from threatware.language.translate import Translate
from threatware.utils.request import Request

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

def _get_default_or_action_override(config:dict, key:str):

    if key is None:
        config_local = config
    else:
        config_local = config.get(key, {})

    # Get the default value (if it exists)
    default_value = config_local.get("default", None)
    # Get the action specific override (if it exists)
    override_value = config_local.get(Request.action, None)

    # If the default value is None, then just return the action specific override (which may also be None)
    if default_value is None:
        return override_value
    
    # Otherwise combine the default value and the action specific override (if it exists)
    return_value = default_value
    if isinstance(default_value, str):
        # Check if there is an action specific override
        if override_value is not None:
            return override_value
        return return_value
    elif isinstance(default_value, list):
        if override_value is None:
            override_value = []
        return_value.append(override_value)
        return list(set(return_value))  # Remove duplicates
    elif isinstance(default_value, dict):
        if override_value is None:
            override_value = {}
        return return_value | override_value  # Combine the dictionaries, with the action specific override taking precedence
    else:
        logger.error(f"The response config for key '{key}' is of an unsupported type")
        
    return None

class HTMLInject:

    def __init__(self, inject_config:dict):
            
        self.location_element = inject_config.get("location", {}).get("element", "")
        self.location_index = inject_config.get("location", {}).get("index", -1)  # By default assume -1, which means append to the end
        self.include_scripts = inject_config.get("include", {}).get("scripts", [])
        if self.include_scripts is None:
            self.include_scripts = []
        self.include_stylesheets = inject_config.get("include", {}).get("stylesheets", [])
        if self.include_stylesheets is None:
            self.include_stylesheets = []
        self.inline_element = inject_config.get("inline", {}).get("element", "")
        self.inline_style = inject_config.get("inline", {}).get("style", "")
        self.inline_script = inject_config.get("inline", {}).get("script", "")

class BannerConfig:

    def __init__(self, banner_config:dict):

        self.htmlinject = HTMLInject(banner_config.get("inject", {}))
        self.missingfindingstextkey = banner_config.get("text-keys", {}).get("missing-findings", "")
        
class FindingsConfig:

    def __init__(self, findings_config:dict):

        self.htmlinject = HTMLInject(findings_config.get("inject", {}))
        self.finding_attribute = findings_config.get("finding-attributes", {}).get("finding-index", "threatwarefinding")
        self.finding_type = findings_config.get("finding-attributes", {}).get("finding-type", "threatwarefinding-type")
        self.finding_class = findings_config.get("finding-attributes", {}).get("finding-class", "threatwarefinding-class")

class SchemeSpecificConfig:

    def __init__(self, scheme_specific:dict):

        self.htmlinject = HTMLInject(scheme_specific.get("inject", {}))
        self.regex = scheme_specific.get("regex", "")

    def matches(self, text:str):
        return re.search(self.regex, text) is not None

class HTMLConfig:

    def __init__(self, html_config:dict):

        self.schemeSpecificConfig = []
        for scheme_specific_entry in html_config.get("scheme-specific", []):
            self.schemeSpecificConfig.append(SchemeSpecificConfig(scheme_specific_entry))

        self.bannerConfig = BannerConfig(html_config.get("banner", {}))
        self.findingsConfig = FindingsConfig(html_config.get("findings", {}))

class FormatConfig:

    def __init__(self, format_config:dict):

        self.formatConfig = format_config

    def get(self):
        return _get_default_or_action_override(self.formatConfig, None)

class HTTPConfig:

    def __init__(self, http_config:dict):

        self.httpConfig = http_config

    def getHeaders(self):
        return _get_default_or_action_override(self.httpConfig, "headers")

RESPONSE_CONFIG_YAML = "response_config.yaml"
    
RESPONSE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(RESPONSE_CONFIG_YAML))

class ResponseConfig:
    """ Loads and store configuration options for Response

    A class that uses yaml files to configure the response.
    """
    def __init__(self):
        
        config = Translate.localiseYamlFile(ConfigBase.getConfigPath(RESPONSE_CONFIG_YAML_PATH))
        response_config = config.get("response-config", {})

        self.htmlConfig = HTMLConfig(response_config.get("html", {}))
        self.template_text_file = response_config.get("output").get("template-text-file")
        self.format = FormatConfig(response_config.get("format", {}))
        self.http = HTTPConfig(response_config.get("http", {}))
        
