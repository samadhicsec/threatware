#!/usr/bin/env python3
"""
Loads YAML
"""

import logging
from utils.error import ThreatwareError
#from pathlib import Path
from ruamel.yaml import YAML

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def yaml_file_to_dict(path:str):

    yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    logger.debug("Loading YAML '{}'".format(path))

    try: 
        file = open(path, 'r')
    except OSError:
        raise ThreatwareError

    #with open(str(Path(__file__).absolute().parent.joinpath(path)), 'r') as file:
    #with open(path, 'r') as file:
    with file:
        yamldict = yaml.load(file)
        return yamldict

def yaml_str_to_dict(yamlstr:str):

    yaml=YAML(typ='safe') 
    yamldict = yaml.load(yamlstr)
    return yamldict