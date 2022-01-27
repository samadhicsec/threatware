#!/usr/bin/env python3
"""
Validates whether a value matches a value from the template
"""

import logging
from pathlib import Path
import data.find as find
import utils.match as match
from data.key import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def validate(config:dict, key:Key, value:str, references:dict) -> bool:
    
    # Need to get some config from references
    if not (key_tag := references['validator-tag']):
        logger.error("The references parameter did not have a 'validator-tag' key")
        return False

    if not (template_model := references['template-model']):
        logger.error("The references parameter did not have a 'template-model' key")
        return False
    
    tagged_data = find.keys_with_tag(template_model, key_tag)
    
    match_found = False
    for tagged_key, tagged_value in tagged_data:

        # Lots of keys could be tagged as being validated from template, but we only want to look at template values for keys with the same name as the one
        # we are validating (could still possibly lead to issues)
        if tagged_key == key and match.equals(value, tagged_value):
            match_found = True
            break
    
    #if not match_found:
    #    tagged_values = [tagged_value for _, tagged_value in tagged_data]
    #    key.addProperty(references['validator-tag'], config["output_text_invalid"].format(key, value, tagged_values))

    return match_found