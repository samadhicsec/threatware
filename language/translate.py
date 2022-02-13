#!/usr/bin/env python3
"""
Translate class responsible for localisation
"""

import logging
from pathlib import Path
from utils import match
from utils.load_yaml import yaml_file_to_dict, yaml_templated_file_to_dict
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

TRANSLATE_CONFIG_YAML = "translate.yaml"
TRANSLATE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(TRANSLATE_CONFIG_YAML))

class Translate:
    def __init__(self, languageCode:str = ""):

        yaml_config_dict = yaml_file_to_dict(TRANSLATE_CONFIG_YAML_PATH)

        if not match.is_empty(languageCode):
            yaml_config_dict = yaml_config_dict.get(languageCode, yaml_config_dict)

        self.values = yaml_config_dict.get("values", {})

    def localiseYamlFile(self, filepath:Path) -> dict:
       return yaml_templated_file_to_dict(filepath, self.values)