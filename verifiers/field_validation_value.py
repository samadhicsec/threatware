#!/usr/bin/env python3
"""
Verifies that all keys tagged as requiring value validation have valid values
"""

from data import find
import logging
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierIssue
from validators.validators import Validator
from validators.validator_output import ValidatorOutput
from utils import match

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    validator_config = verifier_config.get("validator-config", {})
    vlad = Validator(validator_config)

    non_mandatory_tag = verifier_config["not-mandatory-tag"]

    # Since a tagged key may have several validators configured (we OR the output), we don't find by tag,
    # but rather find by "validate-.*" glob, and then check each validator (as long as they are listed in config)

    # Need to get all keys for a given tag
    tagged_data = find.keys_with_tag_matching_regex(model, "^validate\\-.*$")

    configured_validators = verifier_config["tags"]
    logger.info(f"Configured validators in verifier config - {configured_validators}")

    references = {}
    references['model'] = model
    references['template-model'] = template_model

    for tagged_key, tagged_value in tagged_data:

        if match.is_empty(tagged_value) and tagged_key.hasTag(non_mandatory_tag):
            # Validations should be designed to fail with an empty value, but that's a problem if the value is not mandatory, 
            # so validations still succeed for empty values if the configured 'not-mandatory-tag' tag is present on the key
            continue

        tagged_value_validates = False
        a_validator_failed = False
        validatorOutput_list =[]

        # For each configured validator, check if it is a tag on the current key
        tagged_key_validator = [v for v in configured_validators if tagged_key.hasTag(v["tag"])]
        logger.debug(f"Validators configured for key '{tagged_key.name}' - {tagged_key_validator}")

        # Since we get data passed on tag prefix and not configured validators, it's possible that this tagged data has no configured validator.  No validator means no error
        at_least_one_validator_ran = False
        
        for validator_entry in tagged_key_validator:

            at_least_one_validator_ran = True

            validatorOutput = vlad.validate(validator_entry["tag"], tagged_key, tagged_value, references)

            # Culmultatively record success
            tagged_value_validates = tagged_value_validates or validatorOutput.result

            # Track if a validator fails though
            if not validatorOutput.result:
                a_validator_failed = True

            # Gather the responses from each validator so we can report them in the error
            validatorOutput_list.append(validatorOutput)
        
        issue_dict = {}
        issue_dict["issue_key"] = tagged_key
        issue_dict["issue_value"] = tagged_value
        issue_dict["errordata"] = validatorOutput_list

        if at_least_one_validator_ran:
            if not tagged_value_validates:    
                verify_return_list.append(VerifierIssue("value-invalid", 
                                                        None,
                                                        issue_dict))
            elif a_validator_failed:
                verify_return_list.append(VerifierIssue("value-valid", 
                                                        None,
                                                        issue_dict,
                                                        ErrorType.INFO))

    return verify_return_list