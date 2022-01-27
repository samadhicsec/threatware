#!/usr/bin/env python3
"""
Verifies that all keys tagged with references actually reference something
"""
from pickle import FALSE
from data import find
import logging
from data.key import key as Key
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierIssue
import verifiers.reference as reference
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def reference_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    # TODO this just checks the value endswith the value from where it has a tag referencing, but reallyt we should check for a complete
    # text match e.g. "All assets stored in environment variables"
    if tag_comparison == "template-approved":
        preApproved = compare_to_key.getProperty("templatePreApproved")
        if preApproved is not None and match.equals(compare_value, compare_to_value):
            return True

    return False


def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    doc_reference_tag_prefix = common_config["references"]["doc-tag-prefix"]
    template_reference_tag_prefix = common_config["references"]["templ-tag-prefix"]

    # Find every key with a tag that starts with the configured prefix.
    all_reference_tagged_keys = find.keys_with_tag_matching_regex(model, "^(" + doc_reference_tag_prefix + "|" + template_reference_tag_prefix + ").*$")
           
    for key_entry, value_entry in all_reference_tagged_keys:

        # A quick sanity check that the value entry is a string
        if not isinstance(value_entry, str):
            logger.warning(f"A reference tag was applied to a field ('{key_entry.name}') whose value ('{value_entry}') is not a string. Ignoring.")
            continue
        
        # A key value might be allowed to reference several other fields e.g. asset might be functional or technical,
        # so success boolean will be true if any of the references is valid

        doc_reference_found = reference.check_reference(model, doc_reference_tag_prefix, key_entry, value_entry, None, None)
        doc_section_field_unref_error = []
        if not doc_reference_found:
            doc_section_field_unref_error = reference.get_reference_descriptions(model, doc_reference_tag_prefix, key_entry)

        template_reference_found = reference.check_reference(template_model, template_reference_tag_prefix, key_entry, value_entry, reference_callback, None)
        template_section_field_unref_error = []
        if not template_reference_found:
            template_section_field_unref_error = reference.get_reference_descriptions(template_model, template_reference_tag_prefix, key_entry)

        if not doc_reference_found and not template_reference_found:
            
            issue_dict = {}
            issue_dict["issue_key"] = key_entry
            issue_dict["issue_value"] = value_entry
            issue_dict["fixdata"] = {}
            if len(doc_section_field_unref_error) > 0:
                issue_dict["fixdata"]["document"] = doc_section_field_unref_error
            if len(template_section_field_unref_error) > 0:
                issue_dict["fixdata"]["template"] = template_section_field_unref_error

            verify_return_list.append(VerifierIssue("reference-not-found", 
                                                    "reference-not-found-fix", 
                                                    issue_dict
                                                    ))

    return verify_return_list