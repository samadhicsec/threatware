#!/usr/bin/env python3
"""
Loads validators dynamically
"""

from utils.error import ValidatorsError
import logging
import importlib
from pathlib import Path
from utils.config import ConfigBase
from language.translate import Translate
from utils.load_yaml import yaml_file_to_dict
from data.key import key as Key
from validators.validator_output import ValidatorOutput

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class Validator:
    """ Invokes a range of different configurable, extendable validation methods

    A class that uses 2 yaml files to configure and discover validation methods, that can then be invoked on values
    depending on the 'tags' associated with the value.
    """

    VALIDATORS_YAML = "validators_dispatch.yaml"
    VALIDATOR_CONFIG_YAML = "validators_config.yaml"
    VALIDATORS_TEXT_YAML = "validators_text.yaml"

    VALIDATORS_DISPATCH_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VALIDATORS_YAML))
    VALIDATOR_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VALIDATOR_CONFIG_YAML))
    VALIDATORS_TEXT_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VALIDATORS_TEXT_YAML))

    def __init__(self, validators_config:dict = {}):
        #validators_dispatch_yaml_path = validators_config.get("validator-dispatch-yaml-path", self.VALIDATORS_DISPATCH_YAML_PATH)
        # We don't currently want the dispatch yaml to configurable - could be security implications as people who can update config shouldn't necessarily be people who can run code
        validators_dispatch_yaml_path = self.VALIDATORS_DISPATCH_YAML_PATH
        validators_config_yaml_path = ConfigBase.getConfigPath(validators_config.get("validator-config-yaml-path", self.VALIDATOR_CONFIG_YAML_PATH))
        validators_text_yaml_path = ConfigBase.getConfigPath(validators_config.get("validator-text-yaml-path", self.VALIDATORS_TEXT_YAML_PATH))
                
        self.text_dict = self._load_validator_texts(validators_text_yaml_path)
        self.validator_config_dict = self._load_validator_config(validators_config_yaml_path)
        self.dispatch, self.modules = self._load_validator_dispatch(validators_dispatch_yaml_path)
        
        ValidatorOutput.templated_output_texts = self.text_dict
        ValidatorOutput.validator_config = self.validator_config_dict
    

    def _load_validator_texts(self, validator_text_yaml_path) -> dict:

        yaml_config_dict = yaml_file_to_dict(validator_text_yaml_path) 

        if yaml_config_dict.get("validators-text") == None:
            raise ValidatorsError(f"Validators text file '{validator_text_yaml_path}' did not have a root key of 'validators-text'")

        # Convert to a dict for easy lookup
        validators_text_dict = {}
        for entry in yaml_config_dict["validators-text"]:
            if entry.get("tag") == None:
                raise ValidatorsError(f"The validators text file '{validator_text_yaml_path}' entry under the root 'validators-text' is missing a 'tag' key")
            validators_text_dict[entry["tag"]] = entry

        return validators_text_dict


    def _load_validator_config(self, validator_config_yaml_path) -> dict:

        #yaml_config_dict = yaml_templated_file_to_dict(validator_config_yaml_path, self.values_dict) 
        yaml_config_dict = Translate.localiseYamlFile(validator_config_yaml_path) 

        if yaml_config_dict.get("validator-config") == None:
            raise ValidatorsError(f"Validator config file '{validator_config_yaml_path}' did not have a root key of 'validator-config'")

        # Convert to a dict for easy lookup
        validator_config_dict = {}
        for entry in yaml_config_dict["validator-config"]:
            if entry.get("tag") == None:
                raise ValidatorsError(f"A validator config file '{validator_config_yaml_path}' entry under the root 'validator-config' is missing a 'tag' key")
            validator_config_dict[entry["tag"]] = entry

        return validator_config_dict


    def _load_validator_dispatch(self, validator_yaml_path) -> dict:

        #yaml_dict = yaml_to_dict(str(Path(os.getcwd()).joinpath(MAPS_DIR).joinpath(SCHEMES_YAML)))
        yaml_dict = yaml_file_to_dict(validator_yaml_path) 
        
        all_validators = yaml_dict["validators"]
        
        validators_dict = {}
        modules_dict = {}

        for validator_name in all_validators:
            validator_file = all_validators.get(validator_name, "")
            if not validator_file:
                logger.error("Could not find validator file '{}'".format(validator_name))
                continue
    
            module_name = validator_file
            if validator_file.endswith(".py"):
                module_name = Path(__file__).parent.stem + "." + Path(validator_file).stem
            logger.debug("Loading validator file '{}' as module '{}'".format(validator_file, module_name))
    
            # TODO catch ModuleNotFoundError exceptions
            imp = importlib.import_module(module_name)
            if hasattr(imp, "validate") and callable(imp.validate):
                validators_dict[validator_name] = imp.validate
                modules_dict[validator_name] = module_name
            else:
                logger.warning(f"Validator module/file '{module_name}' did not have a 'validate' method")
        
        return validators_dict, modules_dict



    def validate(self, validator_tag:str, key:Key, value:str, references:dict) -> ValidatorOutput:
        """
        Validates a value from a model

        Using the validator_tag parameter and config files, a validator is invoked that validates the value.  
        Success or failure is written as a property of the 'key' parameter under the validator name e.g.
        'validators.date'

        Parameters
        ----------
        validator_tag : str
            The tag that will be looked up in the validator config YAML to get the validator method and config to use
        key : data.key.Key
            The key from the model that had the tag.  Mostly used to report errors.
        value : str
            The value to validate
        references : dict
            A dict that should contain at least a 'template-model' key that contains the 
            template model.  May be customised to contain anything though.

        Returns
        -------
        ValidatorOutput class
        """

        output = ValidatorOutput(validator_tag, key, value)

        # Check the validator tag can be found
        if (validator_entry := self.validator_config_dict.get(validator_tag)) is None:
            logger.error(f"No validator tag '{validator_tag}' is configured")
            output.result = False
            output.error = f"No validator tag '{validator_tag}' is configured"
            return output

        # Check the validator is present
        if validator_entry.get('validator') is None:
            logger.error(f"No 'validator' key is configured for '{validator_tag}'")
            output.result = False
            output.error = f"No 'validator' key is configured for '{validator_tag}'"
            return output

        # Get the validator
        if (validate := self.dispatch.get(validator_entry.get('validator'))) is None:
            logger.error(f"No validator called '{validator_entry['validator']}' is configured")
            output.result = False
            output.error = f"No validator called '{validator_entry['validator']}' is configured"
            return output

        references['validator-tag'] = validator_tag

        # Validate
        logger.info(f"Entering validator '{validator_entry['validator']}'")
        output.result = validate(validator_entry['config'], key, value, references)
        logger.info(f"Exiting validator '{validator_entry['validator']}'")
        
        output.validator_name = validator_entry["validator"]
        output.validator_module = self.modules[validator_entry["validator"]]
        output.description = key.getProperty(validator_tag)

        return output
