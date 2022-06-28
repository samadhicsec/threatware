#!/usr/bin/env python3
"""
Verifies that all keys tagged as unique have a value that is unique
"""

from data import find
import logging
from data.key import key as Key
import utils.keymaster as keymaster
import utils.match as match
import verifiers.reference as reference
from verifiers.verifier_error import VerifierIssue

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def reference_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    key_data_tag_name = callback_config.get("key_data_tag_name")

    if tag_comparison == "value_not_table":
        # Checking that tables don't match, but values do
        if key_data_tag_name != tag_data_tag_name and match.equals(compare_value, compare_to_value):
            return True

    return False

def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    unique_tag_prefix = verifier_config["unique-tag-prefix"]

    previously_referenced = set()

    for key_entry, value_entry in find.keys_with_tag_matching_regex(model, "^" + unique_tag_prefix + ".*$"):

        # A quick sanity check that the value entry is a string
        if not isinstance(value_entry, str):
            logger.warning(f"A uniqueness tag was applied to a field ('{key_entry.name}') whose value ('{value_entry}') is not a string. Ignoring.")
            continue

        # Since non-unique values will always be in at least 2 places, we don't want to report errors for both places as really it's the same issue
        if key_entry in previously_referenced:
            continue

        callback_config = {"key_data_tag_name": keymaster.get_data_tag_for_key(key_entry)}

        referenced = reference.get_references(model, unique_tag_prefix, key_entry, value_entry, reference_callback, callback_config)

        # If len(referenced) > 1 then this key/value has been found in a different section
        # If len(referenced) == 1 then we do an object reference compare ("is") against what was found. reference.get_references will return only the first instance it finds of a matching key/value,
        # so the "referenced[0][1] is not key_entry" will be true when the current 'for' loop is the 2ND instance of the key/value combination i.e. 'for' loop is on duplicate, reference.get_references 
        # returns first instance, and these are different 'key' objects.  This is what finds duplicates in the same section/table
        if len(referenced) > 1 or (len(referenced) == 1 and referenced[0][1] is not key_entry):

            uniq_section_ref = reference.get_reference_descriptions(model, unique_tag_prefix, key_entry)

            referenced_data = [{'table':keymaster.get_section_for_key(key).getProperty("section"), 'column':key.getProperty("colname"), 'value':value} for tag, key, value in referenced if key is not key_entry]

            issue_dict = {}
            issue_dict["issue_key"] = key_entry
            issue_dict["issue_value"] = value_entry
            issue_dict["errordata"] = referenced_data
            issue_dict["fixdata"] = uniq_section_ref
            verify_return_list.append(VerifierIssue("not-unique",
                                                    "not-unique-fix", 
                                                    issue_dict))

            # Record already found duplicates
            previously_referenced.update([ref[1] for ref in referenced])

    return verify_return_list
