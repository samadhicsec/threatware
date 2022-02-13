#!/usr/bin/env python3
"""
Dynamically loads modules
"""

import logging
import importlib
from typing import Tuple
from utils.load_yaml import yaml_file_to_dict
from pathlib import Path

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def load_from_dispatch_yaml(yamlpath:Path, rootkey:str, modulepath:Path, methodname:str) -> Tuple[dict, dict]:
    """ Dynamically loads a module and return a dict of methods"""

    yaml_dict = yaml_file_to_dict(yamlpath) 
        
    all_modules = yaml_dict[rootkey]
    
    methods_dict = {}
    modules_dict = {}

    for module_id, module_name in all_modules.items():

        fq_module_name = module_name
        if module_name.endswith(".py"):
            fq_module_name = modulepath.stem + "." + Path(module_name).stem
        logger.debug(f"Loading module file '{module_name}' as module '{fq_module_name}'")

        # TODO catch ModuleNotFoundError exceptions
        try:
            imp = importlib.import_module(fq_module_name)
        except ModuleNotFoundError as mnfe:
            logger.warning(f"Could not import module '{fq_module_name}'.  Error - {mnfe}")
            continue

        if hasattr(imp, methodname) and callable(getattr(imp, methodname)):
            methods_dict[module_id] = getattr(imp, methodname)
            modules_dict[module_id] = fq_module_name
        else:
            logger.warning(f"Validator module/file '{fq_module_name}' did not have a '{methodname}' method")
    
    return methods_dict, modules_dict