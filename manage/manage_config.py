#!/usr/bin/env python3
"""
Configuration loading for Manage action
"""

import logging
from pathlib import Path
from language.translate import Translate
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

MANAGE_CONFIG_YAML = "manage_config.yaml"
MANAGE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(MANAGE_CONFIG_YAML))

def config(translator:Translate) -> dict:

    yaml_config_dict = translator.localiseYamlFile(MANAGE_CONFIG_YAML_PATH)

    return yaml_config_dict["manage-config"]