#!/usr/bin/env python3
"""
Loads output format confgiuration
"""

import logging
from pathlib import Path
from utils.config import ConfigBase
import re
from language.translate import Translate

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class HTMLInject:

    def __init__(self, inject_config:dict):
            
        self.location_element = inject_config.get("location", {}).get("element", "")
        self.location_index = inject_config.get("location", {}).get("index", "")
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
        
