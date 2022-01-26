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


# def reference_lookup(model:dict, key_data_tag_name:str, key:Key, value, prefix:str, data_tag_models, reference_cache):
    
#     reference_found = False

#     section_field_unref_error = []

#     # For each tag with the prefix (so if any match, it verifies)
#     for key_tag in key.getTags():

#         if not key_tag.startswith(prefix):
#             # A key might have several other tags unrelated to references
#             continue

#         # Split tag into parts
#         tag_parts = key_tag.split("/")
#         tag_prefix = tag_parts[0]
#         tag_data_tag_name = tag_parts[1]
#         tag_field_tag_name = tag_parts[2]
#         tag_comparison = "equals"
#         if len(tag_parts) == 4:
#             tag_comparison = tag_parts[3]


#         # Get the "-data" model that the reference should exist in.
#         tag_data = None
#         tag_data_key = None
#         for tag_data_key_entry, tag_data_value_entry in data_tag_models:
#             if tag_data_key_entry.hasTag(tag_data_tag_name):
#                 tag_data = tag_data_value_entry
#                 tag_data_key = tag_data_key_entry
#         if tag_data is None:
#             logger.warning(f"Could not find '{tag_data_tag_name}' tagged field")
#             continue
#         #print(f"tag_data = {tag_data}")
#         # For a given key, get the prefix value of the tag
#         #tag_prefix = key_tag[:len(key_tag) - len(reference_tag_suffix)]

#         # Find (and cache) all keys and values that have that prefix tag
#         if (referenced_keyvalues := reference_cache.get(key_tag)) is None:
#             referenced_keyvalues = find.keys_with_tag(tag_data, tag_field_tag_name)
#             reference_cache[key_tag] = referenced_keyvalues

#         # Check that the value of the given key matches a found prefix'd key value
#         for ref_key, ref_value in referenced_keyvalues:
#             if ref_key is key:
#                 # We don't want to compare a key to itself
#                 continue
#             if tag_comparison == "endswith":
#                 if match.endswith(value, ref_value):
#                     reference_found = True or reference_found
#             elif tag_comparison == "value_not_table":
#                 # Checking that tables don't match, but values do
#                 if key_data_tag_name != tag_data_tag_name and match.equals(value, ref_value):
#                     reference_found = True or reference_found
#             else:
#                 if match.equals(value, ref_value):
#                     reference_found = True or reference_found
    
#         if (sectionkey := keymaster.get_section_for_key(tag_data_key)) is None:
#             section = tag_data_key.name
#         else:
#             section = sectionkey.getProperty("section")
#         section_field_str = "(" + section + ", " + tag_field_tag_name + ")"
#         if section_field_str not in section_field_unref_error:
#             if not (tag_comparison == "value_not_table" and key_data_tag_name == tag_data_tag_name):
#                 section_field_unref_error.append(section_field_str)

#     return reference_found, section_field_unref_error

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

        #not_unique, section_field_unref_error = reference_lookup(model, key_data_tag_name, key_entry, value_entry, unique_tag_prefix, data_tag_models, reference_cache)

        referenced = reference.get_references(model, unique_tag_prefix, key_entry, value_entry, reference_callback, callback_config)

        if len(referenced) > 1 or (len(referenced) == 1 and referenced[0][1] is not key_entry):

            #uniq_section_ref = [{'table':tablename, 'column':colname} for tablename, colname in reference.get_sections_description(model, unique_tag_prefix, key_entry)]
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

        # Record already founf duplicates
        previously_referenced.update([ref[1] for ref in referenced])

    return verify_return_list

# def verify_old(verifier_config:dict, model:dict, template_model:dict) -> list:

#     verify_return_list = []

#     verifier_name = __file__.split(".")[0]

#     # Get a reference to all the possible error messages that can be returned
#     errorTexts = verifier_config["error-texts"]

#     tagged_data = find.keys_with_tag(model, "document-unique")

#     possible_sections_keys = []
#     for possible_key, possible_value in tagged_data:
#         if (section := keymaster.get_section_for_key(possible_key)) is None:
#             section = possible_key.getProperty("parentKey")
#         possible_text = "(" + section.getProperty("section") + ", " + possible_key.name + ")"
#         if possible_text not in possible_sections_keys:
#             possible_sections_keys.append(possible_text)

#     all_tagged_values = [match.c14n(value) for (_, value) in tagged_data]

#     cache_non_unique = []

#     for tagged_key, tagged_value in tagged_data:

#         if isinstance(tagged_value, str):
#             tagged_value = match.c14n(tagged_value)
#         # Check the tagged_value has not already been found, and check more than 1 exists amongst all tagged values
#         if tagged_value not in cache_non_unique and all_tagged_values.count(tagged_value) > 1:

#             affected_sections = []
            
#             # Find the actual keys of the duplicates and record the sections they are in
#             for possible_key, possible_value in tagged_data:
#                 if match.equals(tagged_value, possible_value):
#                     if (section := keymaster.get_section_for_key(possible_key)) is None:
#                         section = possible_key.getProperty("parentKey")
#                     affected_text = "(" + section.getProperty("section") + ", " + possible_key.name + ")"
#                     if affected_text not in affected_sections:
#                         affected_sections.append(affected_text)

#             cache_non_unique.append(tagged_value)
#             #print(f"Found non unique {tagged_key} with value {tagged_value}, and property value of {tagged_key.getProperty('value')}, property rowID = {tagged_key.getProperty('rowID')}, rowID value = {tagged_key.getProperty('rowID').getProperty('value')}")
#             verify_return_list.append(VerifierError(verifier_config, 
#                                                     verifier_name,
#                                                     errorTexts["document-unique"].format(tagged_value, tagged_key, ",".join(possible_sections_keys), ",".join(affected_sections)), 
#                                                     tagged_key))

#     return verify_return_list