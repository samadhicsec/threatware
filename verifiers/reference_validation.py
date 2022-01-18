#!/usr/bin/env python3
"""
Verifies that all keys tagged with references actually reference something
"""
from pickle import FALSE
from data import find
import logging
from data.key import key as Key
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierError
import verifiers.reference as reference
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


#def reference_lookup(model:dict, key:Key, value, prefix:str, data_tag_models, reference_cache):
    
#    reference_found = False

#    section_field_unref_error = []

    # For each tag with the prefix (so if any match, it verifies)
#    for key_tag in key.getTags():

#        if not key_tag.startswith(prefix):
            # A key might have several other tags unrelated to references
#            continue

        # Split tag into parts
#        tag_parts = key_tag.split("/")
#        tag_prefix = tag_parts[0]
#        tag_data_tag_name = tag_parts[1]
#        tag_field_tag_name = tag_parts[2]
#        tag_comparison = "equals"
#        if len(tag_parts) == 4:
#            tag_comparison = tag_parts[3]


        # Get the "-data" model that the reference should exist in.
#        tag_data = None
#        tag_data_key = None
#        for tag_data_key_entry, tag_data_value_entry in data_tag_models:
#            if tag_data_key_entry.hasTag(tag_data_tag_name):
#                tag_data = tag_data_value_entry
#                tag_data_key = tag_data_key_entry
#        if tag_data is None:
#            logger.warning(f"Could not find '{tag_data_tag_name}' tagged field")
#            continue
        #print(f"tag_data = {tag_data}")
        # For a given key, get the prefix value of the tag
        #tag_prefix = key_tag[:len(key_tag) - len(reference_tag_suffix)]

        # Find (and cache) all keys and values that have that prefix tag
#        if (referenced_keyvalues := reference_cache.get(key_tag)) is None:
#            referenced_keyvalues = find.keys_with_tag(tag_data, tag_field_tag_name)
#            reference_cache[key_tag] = referenced_keyvalues

        # Check that the value of the given key matches a found prefix'd key value
#        for ref_key, ref_value in referenced_keyvalues:
            #print(f"value_entry = {value_entry}, ref_value = {ref_value}")
#            if tag_comparison == "endswith":
#                if match.endswith(value, ref_value):
#                    reference_found = True
#            elif tag_comparison == "storage-expression":
#                if match.endswith(value, ref_value):
#                    reference_found = True
#            else:
#                if match.equals(value, ref_value):
#                    reference_found = True
    
#        if reference_found:
#            break

#        if (sectionkey := keymaster.get_section_for_key(tag_data_key)) is None:
#            section = tag_data_key.name
#        else:
#            section = sectionkey.getProperty("section")
#        section_field_str = "(" + section + ", " + tag_field_tag_name + ")"
#        if section_field_str not in section_field_unref_error:
#            section_field_unref_error.append(section_field_str)

#    return reference_found, section_field_unref_error

def reference_callback(callback_config, comparison_str, compare_value, compare_to_key, compare_to_value):

    # TODO this just checks the value endswith the value from where it has a tag referencing, but reallyt we should check for a complete
    # text match e.g. "All assets stored in environment variables"
    if comparison_str == "template-approved":
        preApproved = compare_to_key.getProperty("templatePreApproved")
        if preApproved is not None and match.equals(compare_value, compare_to_value):
            return True

    return False


def verify(verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    verifier_name = __file__.split(".")[0]

    # Get a reference to all the possible error messages that can be returned
    errorTexts = verifier_config["error-texts"]

    doc_reference_tag_prefix = verifier_config["doc-tag-prefix"]
    template_reference_tag_prefix = verifier_config["templ-tag-prefix"]

    doc_data_tag_models = find.keys_with_tag_matching_regex(model, "^.*-data$")
    #print(f"data_tag_models len = {len(data_tag_models)}")
    template_data_tag_models = find.keys_with_tag_matching_regex(template_model, "^.*-data$")

    doc_reference_cache = {}
    template_reference_cache = {}

    # Find every key with a tag that starts with the configured prefix.
    all_reference_tagged_keys = find.keys_with_tag_matching_regex(model, "^(" + doc_reference_tag_prefix + "|" + template_reference_tag_prefix + ").*$")
           
    for key_entry, value_entry in all_reference_tagged_keys:

        # A quick sanity check that the value entry is a string
        if not isinstance(value_entry, str):
            logger.warning(f"A reference tag was applied to a field ('{key_entry.name}') whose value ('{value_entry}') is not a string. Ignoring.")
            continue
        
        # A key value might be allowed to reference several other fields e.g. asset might be functional or technical,
        # so success boolean will be true if any of the references is valid

        #doc_reference_found, doc_section_field_unref_error = reference_lookup(model, key_entry, value_entry, doc_reference_tag_prefix, doc_data_tag_models, doc_reference_cache)
        doc_reference_found = reference.check_reference(model, doc_reference_tag_prefix, key_entry, value_entry, None, None)
        doc_section_field_unref_error = []
        if not doc_reference_found:
            doc_section_field_unref_error = reference.get_sections_description(model, doc_reference_tag_prefix, key_entry)

        #template_reference_found, template_section_field_unref_error = reference_lookup(template_model, key_entry, value_entry, template_reference_tag_prefix, template_data_tag_models, template_reference_cache)
        template_reference_found = reference.check_reference(template_model, template_reference_tag_prefix, key_entry, value_entry, reference_callback, None)
        template_section_field_unref_error = []
        if not template_reference_found:
            template_section_field_unref_error = reference.get_sections_description(template_model, template_reference_tag_prefix, key_entry)

        if not doc_reference_found and not template_reference_found:
            
            template_section_field_unref_error_edited = []
            for table, entry in template_section_field_unref_error:
                template_section_field_unref_error_edited.append((table + " in template", entry))

            section_field_unref_error = doc_section_field_unref_error + template_section_field_unref_error_edited
            #row_id_key = keymaster.get_row_identifier_key(key_entry)
            verify_return_list.append(VerifierError(verifier_config, 
                                                    verifier_name, 
                                                    errorTexts["reference-not-found"].format(key_entry, value_entry, ",".join([str(sec) for sec in section_field_unref_error])), 
                                                    key_entry))

    return verify_return_list


#def verify_old(verifier_config:dict, model:dict, template_model:dict) -> list:

#    verify_return_list = []

#    verifier_name = __file__.split(".")[0]

    # Get a reference to all the possible error messages that can be returned
#    errorTexts = verifier_config["error-texts"]

#    doc_reference_tag_prefix = verifier_config["doc-tag-prefix"]
#    template_reference_tag_prefix = verifier_config["templ-tag-prefix"]

#    doc_data_tag_models = find.keys_with_tag_matching_regex(model, "^.*-data$")
    #print(f"data_tag_models len = {len(data_tag_models)}")
#    template_data_tag_models = find.keys_with_tag_matching_regex(template_model, "^.*-data$")

#    reference_cache = {}

    # Find every key with a tag that ends in the configured prefix.
#    res = find.keys_with_tag_matching_regex(model, "^" + doc_reference_tag_prefix + ".*$")
    #print(f"res = {res}")
    
#    for key_entry, value_entry in find.keys_with_tag_matching_regex(model, "^" + doc_reference_tag_prefix + ".*$"):
        #print(f"key_entry = {key_entry}")
        
        # A key value might be alloed to reference several other fields e.g. asset might be functional or technical,
        # so success boolean will be true if any of the references is valid
#        reference_found = False

#        section_field_unref_error = []

        # For each tag with the prefix (so if any match, it verifies)
#        for key_tag in key_entry.getTags():

#            if not key_tag.startswith(doc_reference_tag_prefix):
                # A key might have several other tags unrelated to references
#                continue

            # Split tag into parts
#            tag_parts = key_tag.split("/")
#            tag_prefix = tag_parts[0]
#            tag_data_tag_name = tag_parts[1]
#            tag_field_tag_name = tag_parts[2]
#            tag_comparison = "equals"
#            if len(tag_parts) == 4:
#                tag_comparison = tag_parts[3]


            # Get the "-data" model that the reference should exist in.
#            tag_data = None
#            tag_data_key = None
#            for tag_data_key_entry, tag_data_value_entry in doc_data_tag_models:
#                if tag_data_key_entry.hasTag(tag_data_tag_name):
#                    tag_data = tag_data_value_entry
#                    tag_data_key = tag_data_key_entry
#            if tag_data is None:
#                logger.warning(f"Could not find '{tag_data_tag_name}' tagged field")
#                continue
            #print(f"tag_data = {tag_data}")
            # For a given key, get the prefix value of the tag
            #tag_prefix = key_tag[:len(key_tag) - len(reference_tag_suffix)]

            # Find (and cache) all keys and values that have that prefix tag
#            if (referenced_keyvalues := reference_cache.get(key_tag)) is None:
#                referenced_keyvalues = find.keys_with_tag(tag_data, tag_field_tag_name)
#                reference_cache[key_tag] = referenced_keyvalues

            # Check that the value of the given key matches a found prefix'd key value
#            for ref_key, ref_value in referenced_keyvalues:
                #print(f"value_entry = {value_entry}, ref_value = {ref_value}")
#                if tag_comparison == "endswith":
#                    if match.endswith(value_entry, ref_value):
#                        reference_found = True
#                else:
#                    if match.equals(value_entry, ref_value):
#                        reference_found = True
        
#            if reference_found:
#                break

#            if (sectionkey := keymaster.get_section_for_key(tag_data_key)) is None:
#                sectionkey = tag_data_key
#            section_field_str = "(" + sectionkey.name + ", " + tag_field_tag_name + ")"
#            if section_field_str not in section_field_unref_error:
#                section_field_unref_error.append(section_field_str)

#        if not reference_found:
#            verify_return_list.append(VerifierError(verifier_config, 
#                                                    verifier_name, 
#                                                    errorTexts["reference-not-found"].format(key_entry, value_entry, ",".join(section_field_unref_error)), 
#                                                    key_entry))

#    return verify_return_list
