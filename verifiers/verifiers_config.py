#!/usr/bin/env python3
"""
Loads verifiers dynamically
"""

import logging
import importlib
from pathlib import Path
from language.translate import Translate
from utils.load_yaml import yaml_file_to_dict, yaml_templated_file_to_dict

import utils.logging
from verifiers.verifier_error import VerifierIssue
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class VerifiersConfig:
    """ Loads and store configuration options for Verifiers

    A class that uses yaml files to configure and discover verification methods.
    """

    VERIFIERS_DISPATCH_YAML = "verifiers_dispatch.yaml"
    VERIFIER_CONFIG_YAML = "verifiers_config.yaml"
    #VERIFIER_VALUES_YAML = "verifiers_values.yaml"
    #VERIFIER_TEXTS_YAML = "verifiers_texts.yaml"
    #DEFAULT_TAG_MAPPING_YAML = "default_tag_mapping.yaml"
    
    VERIFIERS_DISPATCH_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIERS_DISPATCH_YAML))
    VERIFIER_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_CONFIG_YAML))
    #VERIFIER_VALUES_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_VALUES_YAML))
    #VERIFIER_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_TEXTS_YAML))
    #DEFAULT_TAG_MAPPING_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(DEFAULT_TAG_MAPPING_YAML))

    def __init__(self, verifiers_config:dict, translator:Translate):
        #verifiers_dispatch_yaml_path = verifiers_config.get("verifiers_dispatch_yaml_config", self.VERIFIERS_DISPATCH_YAML_PATH)
        verifiers_dispatch_yaml_path = self.VERIFIERS_DISPATCH_YAML_PATH
        verifiers_config_yaml_path = verifiers_config.get("verifiers_config_yaml_config", self.VERIFIER_CONFIG_YAML_PATH)
        #verifiers_values_yaml_path = verifiers_config.get("verifiers_values_yaml_config", self.VERIFIER_VALUES_YAML_PATH)
        #verifiers_texts_yaml_path = verifiers_config.get("verifiers_texts_yaml_config", self.VERIFIER_TEXTS_YAML_PATH)
        #default_tag_mapping_yaml_path = verifiers_config.get("tag_mapping_yaml_config", self.DEFAULT_TAG_MAPPING_YAML_PATH)
        self.translator = translator

        self.disable = verifiers_config.get("disable", [])
        if self.disable is None:
            self.disable = []

        self.validators_config = verifiers_config.get("validators", {})
        if self.validators_config is None:
            self.validators_config = {}

        #self.verifiers_values_dict = self._load_verifiers_values(verifiers_values_yaml_path)
        self.translations = self.translator.translations
        self.dispatch = self._load_verifiers_dispatch(verifiers_dispatch_yaml_path)
        self.verifiers_config_dict = self._load_verifiers_config(verifiers_config_yaml_path)
        #self.verifiers_texts_dict = self._load_verifiers_texts(verifiers_texts_yaml_path)
        self.verifiers_texts_dict = self._load_verifiers_texts(self.verifiers_config_dict.get("output").get("template-text-file"))
        #self.tag_mapping = self._load_tag_mapping(default_tag_mapping_yaml_path)
        self.tag_mapping = self._load_tag_mapping(self.verifiers_config_dict.get("common").get("default-verifier-tag-mapping"))

    def _load_verifiers_config(self, verifiers_config_yaml_path) -> dict:
        
        #yaml_config_dict = yaml_templated_file_to_dict(verifiers_config_yaml_path, self.verifiers_values_dict)
        yaml_config_dict = self.translator.localiseYamlFile(verifiers_config_yaml_path)

        return yaml_config_dict["verifiers-config"]

    def _load_verifiers_dispatch(self, verifiers_dispatch_yaml_path:str):
        
        yaml_dict = yaml_file_to_dict(verifiers_dispatch_yaml_path) 
        
        all_verifiers = yaml_dict["verifiers-dispatch"]

        verifiers_dict = {}

        for verifier_name in all_verifiers:
            verifier_code = all_verifiers.get(verifier_name, "")
            if verifier_code == "":
                logger.warning(f"No value specified for verifier '{verifier_name}'")
                continue
            
            module_name = verifier_code
            if verifier_code.endswith(".py"):
                module_name = Path(__file__).parent.stem + "." + Path(verifier_code).stem
            logger.debug(f"Loading verifier file '{verifier_code}' as module '{module_name}'")
            # TODO catch ModuleNotFoundError exceptions
            imp = importlib.import_module(module_name)
            if hasattr(imp, "verify") and callable(imp.verify):
                verifiers_dict[verifier_name] = imp.verify
            else:
                logger.warning(f"Verifier file '{verifier_code}' did not have a 'verify' method")

        return verifiers_dict

    # def _load_verifiers_values(self, verifiers_values_yaml_path:str):

    #     return yaml_file_to_dict(verifiers_values_yaml_path) 

    def _load_verifiers_texts(self, verifiers_texts_yaml_path:str):

        return yaml_file_to_dict(verifiers_texts_yaml_path) 

    def _load_tag_mapping(self, tag_mapping_yaml_path) -> list:
    
        yaml_config_dict = yaml_file_to_dict(tag_mapping_yaml_path) 

        return yaml_config_dict["tag-mapping"]