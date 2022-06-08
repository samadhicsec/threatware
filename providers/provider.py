#!/usr/bin/env python3
"""
Abstracts away the execution provider e.g. local, AWS, GCP
"""

import logging
from pathlib import Path
from utils.config import ConfigBase
import utils.match as match
import utils.load_modules as load_modules
from utils.load_yaml import yaml_file_to_dict

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

PROVDERS_CONFIG_YAML = "providers_config.yaml"
PROVIDERS_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(PROVDERS_CONFIG_YAML))

PROVDERS_DISPATCH_YAML = "providers_dispatch.yaml"
PROVIDERS_DISPATCH_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(PROVDERS_DISPATCH_YAML))

def _load_config():

    yaml_config_dict = yaml_file_to_dict(ConfigBase.getConfigPath(PROVIDERS_CONFIG_YAML_PATH))

    return yaml_config_dict.get("providers", {})

def _load_dispatch():

    provider_loaders, _ = load_modules.load_from_dispatch_yaml(PROVIDERS_DISPATCH_YAML_PATH, "providers", Path(__file__).parent, "load")

    return provider_loaders

def get_provider(provider_name:str, no_config_mode:bool = False):

    provider_loaders = _load_dispatch()

    if not no_config_mode:
        provider_config = _load_config()
        return provider_loaders[provider_name](provider_config[provider_name])
    else:
        return provider_loaders[provider_name]({})

    #if match.is_empty(provider_name):
    #    provider_name = provider_config["provider"]

    #return provider_loaders[provider_name](provider_config[provider_name])

