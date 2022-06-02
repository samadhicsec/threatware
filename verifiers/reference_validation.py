#!/usr/bin/env python3
"""
Verifies that all keys tagged with references actually reference something
"""
import logging
from sre_parse import fix_flags
from utils import tags
from data.key import key as Key
from data import find
from verifiers.verifier_error import VerifierIssue
import verifiers.reference as reference
from language.translate import Translate
from utils import match, transform

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# def _strip_context(config:dict, value:str):

#     start_char = config["start-char"]
#     end_char = config["end-char"]

#     if(start_char_index := value.find(start_char)) != -1:
#         if(end_char_index := value.find(end_char, start_char_index)) != -1:
#             return value[:start_char_index] + value[end_char_index + 1:]

#     return value

def template_reference_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    #strip_config = {"start-char":"(", "end-char":")"}
    strip_config = callback_config["strip-context"]

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    if tag_comparison == "template-approved":
        preApproved = compare_to_key.getProperty("templatePreApproved")
        # For pre-approved template values, we allow 'context' to be added in the TM e.g. in-memory (component).  But we strip this when matching to the pre-approved value
        #if preApproved is not None and match.equals(compare_value, compare_to_value, lambda val : _strip_context(strip_config, val)):
        if preApproved is not None and match.equals(compare_value, compare_to_value, transform.strip(strip_config["start-char"], strip_config["end-char"])):
            # TODO: Does not currently validate that the tag of the preApproved value matches the tag of the reference being checked e.g. pre-approved in functional assets table wouldn't match a ref tagged with just the the technical assets table.  This would restrict ref matches, so may not be a good thing.
            return True

    return False

def reference_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    strip_config = callback_config["strip-context"]

    # We want to strip any context for the purpose of copmarison of references
    if match.equals(compare_value, compare_to_value, transform.strip(strip_config["start-char"], strip_config["end-char"])):
        return True

    if tag_comparison == "storage-expression":
        # TODO this just checks the value endswith the value from where it has a tag referencing, but really we should check for a complete
        # text match e.g. "All assets stored in environment variables"
        grouped_text = callback_config.get("grouped-text", {}).get("storage-expression")

        if match.starts_ends(compare_value, Translate.localise(grouped_text, "start-assets-grouped-by-storage"), compare_to_value):
            return True
        if match.equals(compare_value, Translate.localise(grouped_text, "all-assets")):
            return True

    # TODO- make this more generic so you can dynamically add more grouped text.
    if tag_comparison == "asset-expression":
        asset_text = callback_config.get("grouped-text", {}).get("asset-expression")

        if match.equals(compare_value, Translate.localise(asset_text, "all-functional-assets")):
            return True

    return False

def _get_possible_fixed_texts(common_config:dict, key_entry:Key) -> list:

    # For each tag
    for tag in key_entry.getTags():

        tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tags.get_quad_tag_parts(tag)

        # TODO- make this more generic so you can dynamically add more grouped text.
        if tag_comparison == "asset-expression":

            return Translate.localise(common_config["grouped-text"]["asset-expression"], "all-functional-assets")

    return []

def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    doc_reference_tag_prefix = common_config["references"]["doc-tag-prefix"]
    template_reference_tag_prefix = common_config["references"]["templ-tag-prefix"]

    reference_callback_config = {}
    reference_callback_config["grouped-text"] = common_config["grouped-text"]
    reference_callback_config["strip-context"] = common_config["strip-context"]

    # Find every key with a tag that starts with the configured prefix.
    all_reference_tagged_keys = find.keys_with_tag_matching_regex(model, "^(" + doc_reference_tag_prefix + "|" + template_reference_tag_prefix + ").*$")
           
    for key_entry, value_entry in all_reference_tagged_keys:

        # A quick sanity check that the value entry is a string
        if not isinstance(value_entry, str):
            logger.warning(f"A reference tag was applied to a field ('{key_entry.name}') whose value ('{value_entry}') is not a string. Ignoring.")
            continue
        
        # A key value might be allowed to reference several other fields e.g. asset might be functional or technical,
        # so success boolean will be true if any of the references is valid

        doc_reference_found = reference.check_reference(model, doc_reference_tag_prefix, key_entry, value_entry, reference_callback, reference_callback_config)
        doc_section_field_unref_error = []
        if not doc_reference_found:
            doc_section_field_unref_error = reference.get_reference_descriptions(model, doc_reference_tag_prefix, key_entry)

        template_reference_found = reference.check_reference(template_model, template_reference_tag_prefix, key_entry, value_entry, template_reference_callback, reference_callback_config)
        template_section_field_unref_error = []
        if not template_reference_found:
            template_section_field_unref_error = reference.get_reference_descriptions(template_model, template_reference_tag_prefix, key_entry)

        if not doc_reference_found and not template_reference_found:
            
            fixed_texts = _get_possible_fixed_texts(common_config, key_entry)

            issue_dict = {}
            issue_dict["issue_key"] = key_entry
            issue_dict["issue_value"] = value_entry
            issue_dict["fixdata"] = {}
            if len(doc_section_field_unref_error) > 0:
                issue_dict["fixdata"]["document"] = doc_section_field_unref_error
            if len(template_section_field_unref_error) > 0:
                issue_dict["fixdata"]["template"] = template_section_field_unref_error
            if len(fixed_texts) > 0:
                issue_dict["fixdata"]["static-texts"] = fixed_texts

            verify_return_list.append(VerifierIssue("reference-not-found", 
                                                    "reference-not-found-fix", 
                                                    issue_dict
                                                    ))

    return verify_return_list