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

from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader = FileSystemLoader(searchpath=["/", "./"]),
    autoescape=select_autoescape()
)

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

def yaml_templated_str_to_dict(yaml_template_str:str, context:dict):

    templated_yaml = env.from_string(yaml_template_str)

    render_yaml = templated_yaml.render(context)

    return yaml_str_to_dict(render_yaml)

def yaml_templated_file_to_dict(yaml_template_file_path:str, context:dict):

    templated_yaml = env.get_template(yaml_template_file_path)

    render_yaml = templated_yaml.render(context)

    return yaml_str_to_dict(render_yaml)

def class_to_yaml_file(output_classes, output_instance, file_location):

    yaml=YAML(typ='safe')
    yaml.default_flow_style = False
    for output_class in output_classes:
        yaml.register_class(output_class)
    yaml.dump(output_instance, file_location)