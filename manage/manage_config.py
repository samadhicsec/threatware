#!/usr/bin/env python3
"""
Configuration loading for Manage action
"""

import logging
from pathlib import Path
from utils.load_yaml import yaml_file_to_dict
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

MANAGE_CONFIG_YAML = "manage_config.yaml"
MANAGE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(MANAGE_CONFIG_YAML))

def config():

    yaml_config_dict = yaml_file_to_dict(MANAGE_CONFIG_YAML_PATH)

    return yaml_config_dict["manage-config"]