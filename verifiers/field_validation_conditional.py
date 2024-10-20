#!/usr/bin/env python3
"""
Verifies that all keys tagged DON'T have a, maybe specific, value, if some dependent key has a, maybe specific, value.  An opposite to conditional mandatory
"""

from data import find
import logging
from validators.validators import Validator
from verifiers.verifier_error import VerifierIssue
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    validator_obj_config = common_config.get("validator-config", {})
    vlad = Validator(validator_obj_config)

    references = {}
    references['model'] = model
    references['template-model'] = template_model

    verify_return_list = []

    # The config could contain many tagged values to look for
    for conditional in verifier_config["conditionals"]:

        if_value_tag = conditional.get("if", {}).get("value-tag")
        then_value_tag = conditional.get("then", {}).get("value-tag")

        # Create an if_lambda parameterised on the 'if' Key and value
        if_value_condition = conditional.get("if", {}).get("value-condition")
        if_lambda = lambda key, value : vlad.validate_from_config(if_value_condition, key, value, references)

        # Create a then_lambda parameterised on the 'then' Key and value
        then_value_condition = conditional.get("then", {}).get("value-condition")
        then_lambda = lambda key, value : vlad.validate_from_config(then_value_condition, key, value, references)

        # Need to get all keys for a given 'if' tag
        if_tagged_data = find.keys_with_tag(model, if_value_tag)

        for if_tagged_key, if_tagged_value in if_tagged_data:
            # Get the rowID for the 'if' tagged key
            rowIDkey = keymaster.get_row_identifier_for_key(if_tagged_key)
            row_data = rowIDkey.getProperty("row")
            
            # Get the 'then' key and value
            then_tagged_key, then_tagged_value = find.key_with_tag(row_data, then_value_tag)

            # If the 'if' clause is true, but the 'then' clause is false, then that is a finding
            if if_lambda(if_tagged_key, if_tagged_value) and not then_lambda(then_tagged_key, then_tagged_value):

                issue_dict = {}
                issue_dict["issue_key"] = then_tagged_key
                issue_dict["issue_value"] = then_tagged_value
                if (issue_location := conditional.get("issue-location", None)) is not None:
                    # Override which of the 'if'/'then' keys is the 'issue_key', as sometimes errors can't report the 'then' key e.g. when testing for existence
                    if (issue_location == "if"):
                        issue_dict["issue_key"] = if_tagged_key
                        issue_dict["issue_value"] = if_tagged_value
                issue_dict["if_key"] = if_tagged_key
                issue_dict["if_value"] = if_tagged_value
                issue_dict["then_key"] = then_tagged_key
                issue_dict["then_value"] = then_tagged_value

                # The actual issue may be located somewhere else, so accomodate overrides to better explain how to fix the issue
                # Allow "issue-table-tag" to be set to allow override
                issue_table_value = model
                if (issue_table_tag := conditional.get("issue-table-tag", None)) is not None:
                    issue_table_key, issue_table_value = find.key_with_tag(model, issue_table_tag)
                    if issue_table_key is not None:
                        if (sectionKey := keymaster.get_section_for_key(issue_table_key)) is not None:
                            issue_dict["issue_table"] = sectionKey.getProperty("section")

                # Allow "issue-table-row" to be 'None' to indicate that no 'Location' is shown in the error
                if (issue_table_row := conditional.get("issue-table-row", 1)) is None:
                    if match.is_empty(issue_table_row):
                        issue_dict["issue_table_row"] = None

                # Use "issue-table-col-tag" to set the "issue_table_col" passed to VerifierIssue
                if (issue_key_tag := conditional.get("issue-table-col-tag", None)) is not None:
                    issue_key_key, _ = find.key_with_tag(issue_table_value, issue_key_tag)
                    if issue_key_key is not None:
                        issue_dict["issue_table_col"] = issue_key_key.getProperty("colname")
                        #issue_dict["issue_key"] = issue_key_key
                        #issue_dict["issue_value"] = None

                verify_return_list.append(VerifierIssue(
                    error_text_key=conditional["issue-text-key"], 
                        fix_text_key=conditional.get("fix-text-key", None), 
                        issue_dict=issue_dict))

    return verify_return_list