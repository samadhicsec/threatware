#!/usr/bin/env python3
"""
Verifies that all assets are covered by a threat
"""
from data import find
import logging
import verifiers.reference as reference
from language.translate import Translate
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierIssue
from utils import match, transform
from utils import tags

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

   
def location_storage_expression_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    if tag_comparison == "storage-expression":
        
        storage_location_value = callback_config.get("storage_location_value")
        if match.equals(storage_location_value, compare_to_value):

            #grouped_text = callback_config.get("grouped-text", {}).get("storage-expression")
            component_transform = callback_config.get("component-transform", transform.identity)

            if match.starts_ends(compare_value, Translate.localise(callback_config.get("output-texts", {}), "start-assets-grouped-by-storage", ignore_format=True), component_transform(compare_to_value)):
                return True
            if match.equals(compare_value, Translate.localise(callback_config.get("output-texts", {}), "all-assets", ignore_format=True)):
                return True
            #if match.endswith(compare_value, compare_to_value):
            #    return True

    return False

def component_storage_expression_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    if tag_comparison == "storage-expression":
        #grouped_text = callback_config.get("grouped-text", {}).get("storage-expression")
        component_transform = callback_config.get("component-transform", transform.identity)

        if match.starts_ends(compare_value, Translate.localise(callback_config.get("output-texts", {}), "start-assets-grouped-by-storage", ignore_format=True), component_transform(compare_to_value)):
            return True
        if match.equals(compare_value, Translate.localise(callback_config.get("output-texts", {}), "all-assets", ignore_format=True)):
            return True

    return False

def template_reference_callback(callback_config, tag_comparison, compare_value, compare_to_key, compare_to_value):

    return False

def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = assets_verify(common_config, verifier_config, model, template_model)

    # Not currently used.  Likely to be deprecated.  Too complicated.
    #verify_return_list.extend(cov_verify(common_config, verifier_config, model, template_model))

    return verify_return_list

def assets_verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:
    verify_return_list = []

    # Get all the data required to do the validation
    tagged_asset_data_list = common_config["asset-tags"]["asset-data-tag"]
    all_assets = []
    for tag in tagged_asset_data_list:
        tag_asset_data_key, tag_asset_data_value = find.key_with_tag(model, tag)
        if not isinstance(tag_asset_data_value, list):
            logger.error(f"Expecting the data tagged with '{tag}' to be a list, but it was a '{type(tag_asset_data_value)}'. Ignoring.")
            continue
    
        all_assets.append((tag, tag_asset_data_key, tag_asset_data_value))

    if len(all_assets) == 0:
        logger.error(f"Could not find any asset data tagged with '{common_config['asset-tags']['asset-data-tag']}'")

    threats_and_controls_key, threats_and_controls_data = find.key_with_tag(model, common_config["threat-tags"]["threats-data-tag"])
    if threats_and_controls_data is None:
        logger.error(f"Could not find threat data tagged with '{common_config['threat-tags']['threats-data-tag']}'")

    # Get a list of in-scope and out-of-scope components
    in_scope_components = []
    out_of_scope_components = []
    components_key, components_data = find.key_with_tag(model, common_config["component-tags"]["component-data-tag"])
    for component_row in components_data:
        component_row_id_key, component_row_id_data = find.key_with_tag(component_row, "row-identifier")
        in_scope_key, in_scope_data = find.key_with_tag(component_row, common_config["component-tags"]["component-in-scope-tag"])
        if match.equals(in_scope_data, common_config["component-tags"]["component-in-scope-value"]):
            in_scope_components.append(component_row_id_data)
        else:
            out_of_scope_components.append(component_row_id_data)

    component_transform = transform.strip(common_config["strip-context"]["start-char"], common_config["strip-context"]["end-char"])

    #callback_config = {"grouped-text":common_config["grouped-text"], "component-transform":component_transform}
    callback_config = {"output-texts":common_config["output-texts"], "component-transform":component_transform}

    exclude_callback = lambda callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value: match.contains(compare_value, compare_to_value)

    # Loop through the asset data tables
    for asset_data_tag, asset_data_key, asset_data_value in all_assets:

        # Loop through the actual rows of assets in a data table
        for asset in asset_data_value:

            # Get the row identifier for the asset (to store covering threats against and for error reporting)
            row_id_key, row_id_data = find.key_with_tag(asset, "row-identifier")
            if row_id_key is None:
                logger.error(f"Could not find a 'row-identifier' tag on any field for asset '{asset}'")

            # Get the storage-locations for the asset
            for storage_location_key, storage_location_value in find.keys_with_tag(asset, common_config["asset-tags"]['asset-location-tag']):

                if match.equals(storage_location_value, out_of_scope_components, component_transform):
                    logger.debug(f"Ignoring threat coverage for asset '{row_id_key.name}' in storage location '{storage_location_value}' as '{storage_location_value}' is out of scope")
                    continue

                # Ignore any excluded values
                exclude = False
                for exclude_tag in tags.get_prefixed_tag(common_config["exclude"]["tag-prefix"] + "/", storage_location_key):
                    exclude_tag_tuple = tags.get_quad_tag_parts(exclude_tag)
                    tag_prefix, tag_type, tag_value, tag_comparison = exclude_tag_tuple
                    
                    if exclude := tags.check_tag_comparison(exclude_tag_tuple, storage_location_value, storage_location_key, tag_value, exclude_callback, None, True):
                        storage_location_key.addProperty("excluded", True)
                        logger.debug(f"Ignoring threat coverage for asset '{row_id_key.name}' in storage location '{storage_location_value}' as tag '{exclude_tag}' excludes it")
                        break
                if exclude:
                    continue

                logger.debug(f"Checking threat coverage for asset '{row_id_key.name}' in storage location '{storage_location_value}'")

                # Add an empty list of covering threats.  The list will be appended to as it is found.
                covering_threats = []
                row_id_key.addProperty(storage_location_key, covering_threats)

                # An asset is covered by a threat when:
                # Scenario A: threat component includes = in-scope asset storage location AND asset = name
                # Scenario B: threat component includes = in-scope asset storage location AND asset = type
                # Scenario C: threat component includes = in-scope asset storage location AND asset = all assets in component
                # Scenario D: threat component is anything AND asset = all assets in known storage type (e.g. env var)
                
                # Try to find a covering threat for the asset in the storage location by searching the threats and controls data
                for entry in threats_and_controls_data:

                    # An entry in the threats data section can contain multiple assets and components
                    
                    # Note, we are just searching the threats row here, so the assets and components returned will be in the same table row
                    threat_asset_entries = find.keys_with_tag(entry, common_config["threat-tags"]["threat-asset-tag"])
                    threat_component_entries = find.keys_with_tag(entry, common_config["threat-tags"]["threat-component-tag"])

                    if len(threat_asset_entries) == 0:
                        # This validation issue will be raised elsewhere
                        continue

                    # Does the storage location for the asset match one of the components?
                    matching_component = match.get_equals(storage_location_value, [component_name for (_, component_name) in threat_component_entries], component_transform)
                    if match.equals(matching_component, in_scope_components, component_transform):
                        matching_in_scope_component = matching_component
                    else:
                        matching_in_scope_component = None

                    for threat_asset_entry_key, threat_asset_entry_value in threat_asset_entries:

                        if matching_in_scope_component is not None:
                            # Scenario A, B, C
                            # Then the asset can match on name or type, but the storage location must match the component
                            
                            # This checks if any 'ref' tag in 'threat_asset_entry_key' can be found in row 'asset' for value 'threat_asset_entry_value'
                            if reference.check_reference_row(asset, "ref", threat_asset_entry_key, threat_asset_entry_value, component_storage_expression_callback, callback_config, only_callback=False) is not None and match.equals(matching_in_scope_component, storage_location_value, component_transform):
                                if entry not in covering_threats:
                                    covering_threats.append(entry)
                        else:
                            # Scenario D
                            # The asset can only match on grouped storage type e.g. All assets stored in env vars
                            callback_config["storage_location_value"] = storage_location_value

                            if (matched_tag := reference.check_reference_row(asset, "ref", threat_asset_entry_key, threat_asset_entry_value, location_storage_expression_callback, callback_config, only_callback=True)) is not None and match.endswith(matched_tag, "storage-expression"):
                                if entry not in covering_threats:
                                    covering_threats.append(entry)

                if len(covering_threats) == 0:
                    issue_dict = {}
                    issue_dict["issue_key"] = row_id_key
                    issue_dict["issue_value"] = row_id_data
                    issue_dict["issue_table"] = threats_and_controls_key.getProperty("section")
                    issue_dict["issue_table_row"] = None    # Disable showing this in the error message
                    #issue_dict["fixdata"] = Translate.localise(common_config["grouped-text"]["storage-expression"], "start-assets-grouped-by-storage")
                    #issue_dict["fixdata"] = common_config["grouped-text"]["storage-expression"]
                    # Need to get some helpful texts relating to the threats and control data
                    # Although we found the issue by looping over asset keys, the problem is in the threats and controls data
                    issue_dict["storage_location"] = storage_location_value
                    issue_dict["threats_and_controls_table"] = threats_and_controls_key.getProperty("section")
                    
                    issue_dict["asset_key"] = None
                    # We need to get information about the key tagged "threat-asset-tag" but have to handle the scenario where no entries have yet been put in the column 
                    if len(threats_and_controls_data) > 0:
                        threat_asset_entries = find.keys_with_tag(threats_and_controls_data, common_config["threat-tags"]["threat-asset-tag"])
                        if len (threat_asset_entries) > 0:
                            for keyentry, valueentry in threat_asset_entries:
                                if not keyentry is None:
                                    issue_dict["asset_key"] = keyentry
                                    break
                    
                    if issue_dict["asset_key"] is None:
                        # We could find a key tagged with "threat-asset-tag"
                        fix_text_key = "no-covering-threat-fix-no-threat-or-asset"
                    else:
                        fix_text_key = "no-covering-threat-fix"

                    verify_return_list.append(VerifierIssue(
                        error_text_key="no-covering-threat", 
                        fix_text_key=fix_text_key, 
                        fix_data_key="start-assets-grouped-by-storage",
                        issue_dict=issue_dict, 
                        errortype=ErrorType.NOT_SET))
            
                else:
                    # Store covering threats
                    storage_location_key.addProperty("covering-threats", covering_threats)

    return verify_return_list

in_scope_components = []
out_of_scope_components = []

def _filter(common_config, model, comparison, covered_key_values):

    filtered_keyvalues = []

    if match.equals(comparison, "equals"):
        return covered_key_values

    if match.equals(comparison, "component_in_scope"):
        if len(in_scope_components) == 0 and len(out_of_scope_components) == 0:
            components_key, components_data = find.key_with_tag(model, common_config["component-tags"]["component-data-tag"])
            for component_row in components_data:
                component_row_id_key, component_row_id_data = find.key_with_tag(component_row, "row-identifier")
                in_scope_key, in_scope_data = find.key_with_tag(component_row, common_config["component-tags"]["component-in-scope-tag"])
                if match.equals(in_scope_data, common_config["component-tags"]["component-in-scope-value"]):
                    in_scope_components.append(component_row_id_data)
                else:
                    out_of_scope_components.append(component_row_id_data)
        
        for key_entry, value_entry in covered_key_values:
            if match.equals(value_entry, in_scope_components):
                filtered_keyvalues.append((key_entry, value_entry))

    return filtered_keyvalues

def cov_verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    # Get all the "cov" references
    # Find every key with a tag that starts with the configured prefix.
    all_cov_tagged_keys = find.keys_with_tag_matching_regex(model, "^cov/.*$")

    all_cov_tagged_keys = [(key, value, tag) for key, value in all_cov_tagged_keys for tag in tags.get_prefixed_tag("cov", key)]
               
    # Group by 'covered' context and 'covering' context
    covered_tagged_keys = [(key, value, tag) for key, value, tag in all_cov_tagged_keys if (tags.get_quad_tag_parts(tag)[1]).startswith("covered") ]
    covering_tagged_keys = [(key, value, tag) for key, value, tag in all_cov_tagged_keys if (tags.get_quad_tag_parts(tag)[1]).startswith("covering") ]

    # For each 'covered' context identifier
    for covered_section_key, covered_section_value, tag in covered_tagged_keys:

        if (section := covered_section_key.getProperty("section")) is None:
            logger.warning(f"Coverage tag '{tag}' was not applied to section.  Ignoring")
            continue

        prefix, context, covered_key_tag, comparison = tags.get_quad_tag_parts(tag)
        if len(context.split("=")) != 2:
            logger.warning(f"Found coverage tag '{context}' with context that didn't include an ID")
            continue
        covered_context_id = context.split("=")[1]

        # Get the covered tagged keys
        covered_key_values = find.keys_with_tag(covered_section_value, covered_key_tag)

        # Filter the covered tagged keys
        covered_key_values = _filter(common_config, model, comparison, covered_key_values)

        # For each 'covering' context with same identifier
        for covering_section_key, covering_section_value, tag in covering_tagged_keys:

            if (section := covering_section_key.getProperty("section")) is None:
                logger.warning(f"Coverage tag '{tag}' was not applied to section.  Ignoring")
                continue

            prefix, context, covering_key_tag, comparison = tags.get_quad_tag_parts(tag)
            if len(context.split("=")) != 2:
                logger.warning(f"Found coverage tag '{context}' with context that didn't include an ID")
                continue
            covering_context_id = context.split("=")[1]

            if not match.equals(covered_context_id, covering_context_id):
                continue

            # Get the covering tagged keys
            covering_key_values = find.keys_with_tag(covering_section_value, covering_key_tag)

            # Filter the covering tagged keys
            covering_key_values_filtered = _filter(common_config, model, comparison, covering_key_values)

            # Check if there is a covering tagged key value that matches each covered tagged key value
            covering_values = [value_entry for key_entry, value_entry in covering_key_values_filtered]

            for key_entry, value_entry in covered_key_values:

                if not match.equals(value_entry, covering_values):
                    # Coverage finding
                    issue_dict = {}
                    issue_dict["issue_key"] = key_entry
                    issue_dict["issue_value"] = value_entry
                    issue_dict["issue_table"] = covering_section_key.getProperty("section")
                    issue_dict["issue_table_row"] = None    # Disable showing this in the error message
                    if len(covering_key_values) > 0:
                        key_eg, _ = covering_key_values[0]
                        issue_dict["covering_col"] = key_eg.getProperty("colname")
                    else:
                        # Best we can do when there is no example of a covering key value
                        issue_dict["covering_col"] = covering_key_tag

                    issue_dict["covering_table"] = covering_section_key.getProperty("section")
                    
                    verify_return_list.append(VerifierIssue(
                        error_text_key=covered_context_id, 
                        fix_text_key=covered_context_id + "-fix", 
                        issue_dict=issue_dict, 
                        errortype=ErrorType.NOT_SET))

    return verify_return_list