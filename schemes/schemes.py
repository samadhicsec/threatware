#!/usr/bin/env python3
"""
Loads a scheme file
"""

import logging
from pathlib import Path
from utils.config import ConfigBase
from utils.load_yaml import yaml_file_to_dict

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

SCHEMES_YAML = "schemes.yaml"
SCHEMES_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(SCHEMES_YAML))

def load_scheme(template_scheme):

    yaml_dict = yaml_file_to_dict(ConfigBase.getConfigPath(SCHEMES_YAML_PATH)) 
    maps = yaml_dict["schemes"]
    
    logger.debug("Looking up scheme file for '{}'".format(template_scheme))
    modelmap_file = maps.get(template_scheme, "")
    if not modelmap_file:
        logger.error("Could not find scheme file for '{}'".format(template_scheme))
        return {}

    #yaml_dict = yaml_file_to_dict(str(Path(__file__).absolute().parent.joinpath(modelmap_file)))
    yaml_dict = yaml_file_to_dict(ConfigBase.getConfigPath(modelmap_file))
    return yaml_dict["scheme"]


# TODO write a validation routine for schemes.  
# For tags:
# - keys tags ending in "-data" should also have a section name
# - keys tags cannpt include a '/' (probably other characters as well) - anything that interferes with parsing, or might be a security issue e.g. {}
# - at least 1 field under a "-data" tagged section should have "row-identifier" set
# - tags of a form prefix/data-tag/entry-tag/method actually have data-tag, entry-tag values that are defined tags.  'method' must also exist.
# - currently must define "functional-asset-data", "technical-asset-data" and "threats-and-controls-data" for coverage validation to work
# For covertor:
# - check each processor defined has correct parameters for data.get, data.map and data.output e.g. 
# -- "inherit_row_above_if_empty" actually references an existing key
# -- "value-replace" match and replacement aren't both the same
# -- "value-extract" has a valid regex
# -- "column-num"/"row-num" are numeric