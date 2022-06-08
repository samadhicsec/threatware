#!/usr/bin/env python3
"""
Configuration loading for Measure action
"""

import logging
from pathlib import Path
from utils.config import ConfigBase
from language.translate import Translate
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

MEASURE_CONFIG_YAML = "measure_config.yaml"
MEASURE_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(MEASURE_CONFIG_YAML))

def config() -> dict:

    yaml_config_dict = Translate.localiseYamlFile(ConfigBase.getConfigPath(MEASURE_CONFIG_YAML_PATH))

    return yaml_config_dict["measure-config"]