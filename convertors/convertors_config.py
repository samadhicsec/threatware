#!/usr/bin/env python3
"""
Configuration loading for Convert action
"""

import logging
from pathlib import Path
from language.translate import Translate
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

MEASURE_CONFIG_YAML = "convertors_config.yaml"
MEASURE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(MEASURE_CONFIG_YAML))

def config() -> dict:

    yaml_config_dict = Translate.localiseYamlFile(MEASURE_CONFIG_YAML_PATH)

    return yaml_config_dict["convertors-config"]