#!/usr/bin/env python3
"""
Validates whether a value exists within a given set of tagged data
"""

import logging
import data.find as find
import utils.match as match
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:
    
    # By default look in the threat model
    if not (model := references['model']):
        logger.error("The references parameter did not have a 'model' key")
        return False
    
    if config.get("template", False):
        # If 'template: True' then look in the template
        if not (model := references['template-model']):
            logger.error("The references parameter did not have a 'template-model' key")
            return False

    # If a 'data-tag' has been set then only look at that data
    if (data_tag := config.get("data-tag", None)) is not None:
        _, model = find.key_with_tag(model, data_tag)

    # Get the key to look for in the model
    if (key_tag := config.get("value-tag", None)) is None:
        logger.error("The config did not have a 'value-tag' key")
        return False
    
    tagged_data = find.keys_with_tag(model, key_tag)
    
    if match.equals(value, [key_value for key_name, key_value in tagged_data]):
        return True
    
    return False