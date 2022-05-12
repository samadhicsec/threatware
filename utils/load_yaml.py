#!/usr/bin/env python3
"""
Loads YAML
"""

import logging
from io import StringIO
from utils.error import ThreatwareError
from ruamel.yaml import YAML

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

##
## Methods to help with reading yaml
##

def yaml_file_to_dict(path:str, output_classes:list = []):

    yaml=YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    yaml.default_flow_style = False
    logger.debug("Loading YAML '{}'".format(path))

    try: 
        file = open(path, 'r')
    except OSError:
        raise ThreatwareError

    #with open(str(Path(__file__).absolute().parent.joinpath(path)), 'r') as file:
    #with open(path, 'r') as file:
    for output_class in output_classes:
        yaml.register_class(output_class)
    
    with file:
        yamldict = yaml.load(file)
        return yamldict

def yaml_file_to_str(path:str):

    try: 
        file = open(path, 'r')
    except OSError:
        raise ThreatwareError

    with file:
        yamlstr = file.read()
        return yamlstr

def yaml_str_to_dict(yamlstr:str):

    yaml=YAML(typ='safe') 
    yamldict = yaml.load(yamlstr)
    return yamldict


##
## Methods to help with outputting yaml files
##

_registered_classes:list = []

def yaml_register_class(class_type):
    """ To output to yaml we need to register classes that do their own YAML serialisation. """
    global _registered_classes
    
    if class_type not in _registered_classes:
        _registered_classes.append(class_type)

def _get_yaml_object():

    yaml=YAML(typ='safe')
    yaml.default_flow_style = False
    yaml.indent = 4
    yaml.sort_base_mapping_type_on_output = False
    for registered_class in _registered_classes:
        yaml.register_class(registered_class)

    return yaml

def class_to_yaml_file(output_instance, file_location):

    yaml = _get_yaml_object()

    yaml.dump(output_instance, file_location)


def class_to_yaml_str(output_instance) -> str:
    """ Output an object in YAML.  Any classes in the object need to be registered using yaml_register_class (and provide the appropriate serialisation methods). """
    
    yaml = _get_yaml_object()

    with StringIO() as buf:
        yaml.dump(output_instance, buf)

        return buf.getvalue()