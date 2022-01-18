#!/usr/bin/env python3
"""
Verifies that all keys tagged as mandatory have a non-empty value
"""

from data import find
import logging
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierError
from utils import match

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def verify(verifier_config:dict, model:dict, template_model:dict) -> list:
    
    verify_return_list = []

    verifier_name = __file__.split(".")[0]

    # Get a reference to all the possible error messages that can be returned
    errorTexts = verifier_config["error-texts"]

    if verifier_config.get("default", True):
        # Inner function here makes it easy to create VerifierError without passing lots of variables
        def traverse_model(model):

            if isinstance(model, dict):
                for dict_key, dict_value in model.items():
                    
                    if not (isinstance(dict_value, dict) or isinstance(dict_value, list)) and (not dict_key.hasTag(verifier_config["exceptions-tag"])):
                        #print(f"key = {dict_key}, value = {dict_value}")
                        if match.is_empty(dict_value):
                            verify_return_list.append(VerifierError(verifier_config, 
                                                    verifier_name,
                                                    errorTexts["missing-mandatory"].format(dict_key), 
                                                    dict_key))
                    if isinstance(dict_value, dict) or isinstance(dict_value, list):
                        traverse_model(dict_value)

            if isinstance(model, list):
                for list_entry in model:
                    traverse_model(list_entry)
                
            return

        # Need to search the entire model looking for empty values
        traverse_model(model)

    else:
        # Need to just those keys marked as "mandatory"

        tagged_data = find.keys_with_tag(model, "mandatory")

        for tagged_key, tagged_value in tagged_data:

            if match.is_empty(tagged_value):
                verify_return_list.append(VerifierError(verifier_config, 
                                            verifier_name,
                                            errorTexts["missing-mandatory"].format(tagged_key), 
                                            tagged_key))


    return verify_return_list