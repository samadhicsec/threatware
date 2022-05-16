#!/usr/bin/env python3
"""
Loads verifiers dynamically
"""

import logging
import importlib
from pathlib import Path
from utils import keymaster
from utils import tags
from verifiers.verifiers_config import VerifiersConfig
import data.find as find
import verifiers.reference as reference

import utils.logging
from verifiers.verifier_error import VerifierIssue
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class Verifiers:
    """ Invokes a range of different configurable, extendable model verification methods

    A class that uses yaml files to configure and discover verification methods, that can then be invoked on models
    depending on the 'tags' associated with the keys of the model.
    """

    # VERIFIERS_DISPATCH_YAML = "verifiers_dispatch.yaml"
    # VERIFIER_CONFIG_YAML = "verifiers_config.yaml"
    # VERIFIER_VALUES_YAML = "verifiers_values.yaml"
    # VERIFIER_TEXTS_YAML = "verifiers_texts.yaml"
    # DEFAULT_TAG_MAPPING_YAML = "default_tag_mapping.yaml"
    
    # VERIFIERS_DISPATCH_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIERS_DISPATCH_YAML))
    # VERIFIER_CONFIG_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_CONFIG_YAML))
    # VERIFIER_VALUES_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_VALUES_YAML))
    # VERIFIER_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(VERIFIER_TEXTS_YAML))
    # DEFAULT_TAG_MAPPING_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(DEFAULT_TAG_MAPPING_YAML))

    #def __init__(self, verifiers_config:dict):
    def __init__(self, config:VerifiersConfig):
        # verifiers_dispatch_yaml_path = verifiers_config.get("verifiers_dispatch_yaml_config", self.VERIFIERS_DISPATCH_YAML_PATH)
        # verifiers_config_yaml_path = verifiers_config.get("verifiers_config_yaml_config", self.VERIFIER_CONFIG_YAML_PATH)
        # verifiers_values_yaml_path = verifiers_config.get("verifiers_values_yaml_config", self.VERIFIER_VALUES_YAML_PATH)
        # verifiers_texts_yaml_path = verifiers_config.get("verifiers_texts_yaml_config", self.VERIFIER_TEXTS_YAML_PATH)
        # default_tag_mapping_yaml_path = verifiers_config.get("tag_mapping_yaml_config", self.DEFAULT_TAG_MAPPING_YAML_PATH)

        # self.disable = verifiers_config.get("disable", [])
        # if self.disable is None:
        #     self.disable = []

        # self.validators_config = verifiers_config.get("validators", {})
        # if self.validators_config is None:
        #     self.validators_config = {}
        
        # self.verifiers_values_dict = self._load_verifiers_values(verifiers_values_yaml_path)
        # self.dispatch = self._load_verifiers_dispatch(verifiers_dispatch_yaml_path)
        # self.verifiers_config_dict = self._load_verifiers_config(verifiers_config_yaml_path)
        # self.verifiers_texts_dict = self._load_verifiers_texts(verifiers_texts_yaml_path)
        # self.tag_mapping = self._load_tag_mapping(default_tag_mapping_yaml_path)

        self.config = config

        VerifierIssue.issue_config = self.config.verifiers_config_dict.get("common", {}).get("errors", VerifierIssue.issue_config)
        #VerifierIssue.templated_translations = self.config.translations
        VerifierIssue.templated_error_texts = self.config.verifiers_texts_dict.get("output-texts", {})

    # def _load_verifiers_config(self, verifiers_config_yaml_path) -> dict:
        
    #     #yaml_config_dict = yaml_file_to_dict(verifiers_config_yaml_path) 
    #     yaml_config_dict = yaml_templated_file_to_dict(verifiers_config_yaml_path, self.verifiers_values_dict)

    #     return yaml_config_dict["verifiers-config"]

    # def _load_verifiers_dispatch(self, verifiers_dispatch_yaml_path:str):
        
    #     #yaml_dict = yaml_to_dict(str(Path(os.getcwd()).joinpath(MAPS_DIR).joinpath(SCHEMES_YAML)))
    #     yaml_dict = yaml_file_to_dict(verifiers_dispatch_yaml_path) 
        
    #     all_verifiers = yaml_dict["verifiers-dispatch"]

    #     verifiers_dict = {}

    #     for verifier_name in all_verifiers:
    #         verifier_code = all_verifiers.get(verifier_name, "")
    #         if verifier_code == "":
    #             logger.warning(f"No value specified for verifier '{verifier_name}'")
    #             continue
            
    #         module_name = verifier_code
    #         if verifier_code.endswith(".py"):
    #             module_name = Path(__file__).parent.stem + "." + Path(verifier_code).stem
    #         logger.debug(f"Loading verifier file '{verifier_code}' as module '{module_name}'")
    #         # TODO catch ModuleNotFoundError exceptions
    #         imp = importlib.import_module(module_name)
    #         if hasattr(imp, "verify") and callable(imp.verify):
    #             verifiers_dict[verifier_name] = imp.verify
    #         else:
    #             logger.warning(f"Verifier file '{verifier_code}' did not have a 'verify' method")

    #     return verifiers_dict

    # def _load_verifiers_values(self, verifiers_values_yaml_path:str):

    #     return yaml_file_to_dict(verifiers_values_yaml_path) 

    # def _load_verifiers_texts(self, verifiers_texts_yaml_path:str):

    #     return yaml_file_to_dict(verifiers_texts_yaml_path) 

    # def _load_tag_mapping(self, tag_mapping_yaml_path) -> list:
    
    #     yaml_config_dict = yaml_file_to_dict(tag_mapping_yaml_path) 

    #     return yaml_config_dict["tag-mapping"]

    def verify(self, model:dict, template_model:dict) -> list:
        """
        Executes a range of configured verifier methods on a model.

        Using the tags assigned to keys (and assigning the configured default tags to named keys), a range of verifiers are 
        invoked (can be individually disabled as well) that look for verification errors.

        Parameters
        ----------
        model : dict
            The model where the dict keys are a data.key.Key that supports having tags
        temaplate_model : dict
            The template for the model that contains known good values

        Returns
        -------
        list : A list of VerifierError objects represents the issues discovered by the invoked verifiers
        """

        self.assign_key_tags(model)
        self.assign_row_identifiers(None, model)
        self.assign_key_tags(template_model)
        self.assign_template_pre_approved(template_model)

        verifier_errors_list = []

        common_config = self.config.verifiers_config_dict["common"]
        common_config["grouped-text"] = self.config.verifiers_texts_dict["grouped-text"]

        for verifier in self.config.dispatch:

            if verifier in self.config.disable:
                logger.warning(f"Verifier '{verifier}' has not been run because it was configured as disabled")

            verifier_config = self.config.verifiers_config_dict[verifier]

            logger.info(f"Entering verifier '{verifier}'")

            errors_list = self.config.dispatch[verifier](common_config, verifier_config, model, template_model)

            logger.info(f"Exiting verifier '{verifier}'")

            # Update errors to provide more useful output information
            for error in errors_list:
                error.verifier = verifier

            verifier_errors_list.extend(errors_list)

        return verifier_errors_list

    def assign_key_tags(self, model:dict):
        """
        Assigns default tags to data.key.Keys in a model.  Tags are the basis for verifiers.

        Using the tag mapping file configured in the verifier config (or a default), tags are (only) added
        to model keys.  It's possible to tag keys with 'no-defaults' to avoid default keys being added.

        Parameters
        ----------
        model : dict
            The model where the dict keys are a data.key.Key that supports having tags

        Returns
        -------
        Nothings.  Keys are updated in place.
        """

        tags_list = self.config.tag_mapping

        tags_dict = {}
        # Create dict of tags key-name (as key) and tags list (as value) to easily match on key-name
        for tag_entry in tags_list:
            tags_dict[tag_entry["key-name"]] = tag_entry["tags"]
        
        def _assign_tags(parentKey, model):

            if isinstance(model, dict):
                for dict_key, dict_value in model.items():
                    dict_key.addProperty("parentKey", parentKey)
                    if dict_key.name in tags_dict:
                        if not dict_key.hasTag("no-defaults"):
                            # Append the tags
                            dict_key.addTags(tags_dict[dict_key.name])

                            # We want to record the value of "-data" tagged nodes, as these will be required for some verifiers.
                            #for tag_entry in tags_dict[dict_key.name]:
                            #    if tag_entry.endswith("-data"):
                            #        dict_key.addProperty("value", dict_value)
                            #        break
                                
                    if isinstance(dict_value, dict) or isinstance(dict_value, list):
                        _assign_tags(dict_key, dict_value)

            if isinstance(model, list):
                for list_entry in model:
                    if isinstance(list_entry, dict) or isinstance(list_entry, list):
                        _assign_tags(parentKey, list_entry)
                
            return

        # Create recursive function that for each dict key checks if a tag from the file needs to be added.
        _assign_tags(None, model)

        return

    # In order to report the location of verification errors we need to tag keys with the rows they are in
    def assign_row_identifiers(self, rowIDKey, model):

        if isinstance(model, dict):
            for dict_key, dict_value in model.items():
                # We dont know where in the hierarchy we are, but for dicts we just add the rowIDKey
                if rowIDKey is not None:
                    dict_key.addProperty("rowID", rowIDKey)
                            
                if isinstance(dict_value, dict) or isinstance(dict_value, list):
                    self.assign_row_identifiers(rowIDKey, dict_value)

        if isinstance(model, list):
            # This could be a row, let's try and find a "row-identifier" tag
            for list_entry in model:
                if isinstance(list_entry, dict):
                    local_rowIDKey = rowIDKey
                    # Rows are stored as dict
                    for dict_key, dict_value in list_entry.items():
                        if dict_key.hasTag("row-identifier"):
                            #print(f"Found key tagged with 'row-identifier - {dict_key}")
                            # We found a "row-identifier" for an entry in this row, let's use that from now on
                            local_rowIDKey = dict_key
                            # We need to report errors with the value for the "row-identiifer" key, so let's store the value as a property of the key
                            dict_key.addProperty("value", dict_value)
                            # We need to be able to get sibling data in a row, so also store a reference to the whole row against the 'row-identifier' key
                            dict_key.addProperty("row", list_entry)

                            # There should only be 1 row-identifier per row
                            break
                    # Let's assign the the rowIDKey to all elements of this row (the 'row-identifier' field might not have been the first)
                    # This will include child elements as well
                    self.assign_row_identifiers(local_rowIDKey, list_entry)
                else:
                    # Not a row so recurse using existing rowIDKey
                    self.assign_row_identifiers(rowIDKey, list_entry)
            
        return


    def assign_template_pre_approved(self, template_model:dict):
        """ 
        Extracts from the template pre-approved values that can be used in the threat model
        
        A pre-approved value is a value that should be a reference to another value, but that DOESN'T verify.  The idea being that values
        that are actual references should be included in the TM, but the ones that don't should be treated as pre-approved.  Pre-approved
        values are useful so can list types of data and we don't have to list common components.
        """

        #preApproved = {}

        # Search the template for key ending in the template prefix
        for key_entry, value_entry in find.keys_with_tag_matching_regex(template_model, "^" + self.config.verifiers_config_dict["common"]["references"]["templ-tag-prefix"] + ".*$"):

            if value_entry == "":
                continue

            # Check whether that key value references a value in the template (in this case the template is the doc, so we use the doc prefix)
            if not reference.check_reference(template_model, self.config.verifiers_config_dict["common"]["references"]["doc-tag-prefix"], key_entry, value_entry, None, None):
                # No match.  So since this value does not correctly reference a value in the template, it must be a value added to the template
                # that the template authors want to provide as an option for TM authors to use, without having to properly reference it

                # Get the tags on this key that match the template reference
                data_section_tag = keymaster.get_data_tag_for_key(key_entry)
                matching_tags = tags.get_matching_tags(key_entry, self.config.verifiers_config_dict["common"]["references"]["templ-tag-prefix"], data_section_tag, "", "")

                # Set a property on the template key, marking it as a pre-approved value
                key_entry.addProperty("templatePreApproved", matching_tags)
                #for tag in matching_tags:
                #    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = reference.get_ref_tag_parts(tag)
                #    tag_dict_key = tag_data_tag_name + "/" + tag_field_tag_name
                #    if preApproved.get(tag_dict_key) is None:
                #        preApproved[tag_dict_key] = []
                #    if value_entry not in preApproved[tag_dict_key]:
                #        preApproved[tag_dict_key].append(value_entry)
                # Get all the values that didn't match and add them to our preApproved store
                #reference.get_values_for_tags(template_model, matching_tags, preApproved)

        #return preApproved