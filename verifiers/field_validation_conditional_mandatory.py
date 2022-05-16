#!/usr/bin/env python3
"""
Verifies that all kets tagged as mandatory have a non-empty value, if some dependent key also has a value
"""

from data import find
import logging
from verifiers.verifier_error import VerifierIssue
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    # The config could contain many tagged values to look for
    for tag_entry in verifier_config["tags"]:
        
        # Need to get all keys for a given tag
        tagged_data = find.keys_with_tag(model, tag_entry["tag"])
        #print(f"tagged_data = {tagged_data}")

        for tagged_data_entry_key, tagged_data_entry_value in tagged_data:
            # Get the rowID for the tagged key
            rowIDkey = keymaster.get_row_identifier_for_key(tagged_data_entry_key)
            row_data = rowIDkey.getProperty("row")
            depends_on_key, depends_on_key_value = find.key_with_tag(row_data, tag_entry["depends-on"])
            # 1st clause: does the depend_on value match, and is the tagged_key value empty -> then finding
            # 2nd clause: is there no depend_on value specified, and if the tagged_key value is not empty (i.e. it has a value) -> then finding
            if (("depends-on-value" in tag_entry and match.equals(depends_on_key_value, tag_entry["depends-on-value"])) and match.is_empty(tagged_data_entry_value)) or \
                (("depends-on-value" not in tag_entry and not match.is_empty(depends_on_key_value)) and match.is_empty(tagged_data_entry_value)) :
                issue_dict = {}
                issue_dict["issue_key"] = tagged_data_entry_key
                issue_dict["issue_value"] = tagged_data_entry_value
                issue_dict["depends_on_key"] = depends_on_key
                issue_dict["depends_on_value"] = depends_on_key_value
                if "depends-on-value" in tag_entry:
                    verify_return_list.append(VerifierIssue("missing-conditional-mandatory",
                                                        None, 
                                                        issue_dict))
                else:
                    verify_return_list.append(VerifierIssue("missing-conditional-mandatory-any-value",
                                                        None, 
                                                        issue_dict))


        # # Since we need to look at adjacent fields for the condition, get a list of all sections containing tagged data.  A section is like a table
        # tagged_data_section_list = []
        # for tagged_data_entry_key, tagged_data_entry_value in tagged_data:

        #     # TODO: adding sections is not mandatory, so using them isn't reliable
        #     # Get section that contains that tag
        #     sectionKey = keymaster.get_section_for_key(tagged_data_entry_key)
        #     if sectionKey is not None and sectionKey.getProperty("section") is not None and sectionKey not in tagged_data_section_list:
        #         tagged_data_section_list.append(sectionKey)
        # #print(f"tagged_data_section_list = {tagged_data_section_list}")

        # # For each list entry in the section, find the 2 fields that depend on each other (so we are assuming each section contains a list or dict)
        # for data_section in tagged_data_section_list:
        #     if not (data_section_value := data_section.getProperty("value")):
        #         logger.error(f"Discovered section {data_section} did not have a property 'value'")
        #         continue

        #     if isinstance(data_section_value, dict):
        #         data_section_value = [data_section_value]
        #     #print(f"data_section_value = {data_section_value}")
        #     # The section must be a list and the list entries must be dicts, one key of which must be the tagged data
        #     for dict_entry in data_section_value:
        #         if tag_entry["tag"] in dict_entry and tag_entry["depends-on"] in dict_entry:
        #             # Check if the 'depends-on' field has the necessary value and check the target value exists
        #             if match.equals(dict_entry[tag_entry["depends-on"]], tag_entry["depends-on-value"]) and \
        #                 match.is_empty(dict_entry[tag_entry["tag"]]):
        #                 # Need to get the tagged key to give to the VerifierError
        #                 dict_key_list = list(dict_entry.keys())
        #                 tagged_key = dict_key_list.pop(dict_key_list.index(tag_entry["tag"]))

        #                 verify_return_list.append(VerifierError(verifier_config, 
        #                                             verifier_name,
        #                                             errorTexts["missing-conditional-mandatory"].format(tag_entry["depends-on"], tag_entry["depends-on-value"], tag_entry["tag"]), 
        #                                             tagged_key))

    return verify_return_list