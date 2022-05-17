#!/usr/bin/env python3
"""
Verifies that all keys tagged as mandatory have a non-empty value
"""

from data import find
import logging
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierIssue
from utils import match
from utils.model import recurse

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:
    
    verify_return_list = []

    if verifier_config.get("default", True):

        def _inner_is_empty(key, value, context):
            is_empty = False
            if not key.hasTag(verifier_config["exceptions-tag"]):
                if isinstance(value, str):
                    if match.is_empty(value):
                        is_empty = True
                if isinstance(value, dict) or isinstance(value, list):
                    if len(value) == 0:
                        is_empty = True
            
            if is_empty:
                issue_dict = {}
                issue_dict["issue_key"] = key
                issue_dict["issue_value"] = value
                verify_return_list.append(VerifierIssue("missing-mandatory", 
                                                        None,
                                                        issue_dict))
                return True, True
            else:
                return True, False

        recurse(model, _inner_is_empty, None)

        # Inner function here makes it easy to create VerifierIssue without passing lots of variables
        # def traverse_model(model):

        #     if isinstance(model, dict):
        #         for dict_key, dict_value in model.items():
                    
        #             if not (isinstance(dict_value, dict) or isinstance(dict_value, list)) and (not dict_key.hasTag(verifier_config["exceptions-tag"])):
        #                 #print(f"key = {dict_key}, value = {dict_value}")
        #                 if match.is_empty(dict_value):
        #                     issue_dict = {}
        #                     issue_dict["issue_key"] = dict_key
        #                     issue_dict["issue_value"] = dict_value
        #                     verify_return_list.append(VerifierIssue("missing-mandatory", 
        #                                                             None,
        #                                                             issue_dict))
        #             if isinstance(dict_value, dict) or isinstance(dict_value, list):
        #                 traverse_model(dict_value)

        #     if isinstance(model, list):
        #         for list_entry in model:
        #             traverse_model(list_entry)
                
        #     return

        # # Need to search the entire model looking for empty values
        # traverse_model(model)

    else:
        # Need to just those keys marked as "mandatory"

        tagged_data = find.keys_with_tag(model, "mandatory")

        for tagged_key, tagged_value in tagged_data:

            if match.is_empty(tagged_value):
                issue_dict = {}
                issue_dict["issue_key"] = tagged_key
                issue_dict["issue_value"] = tagged_value
                verify_return_list.append(VerifierIssue("missing-mandatory", 
                                            None,
                                            issue_dict
                                            ))


    return verify_return_list