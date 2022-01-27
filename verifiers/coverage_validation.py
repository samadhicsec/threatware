#!/usr/bin/env python3
"""
Verifies that all assets are covered by a threat
"""
from data import find
import logging
import verifiers.reference as reference
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierIssue
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

   
def doc_reference_callback(callback_config, tag_tuple, compare_value, compare_to_key, compare_to_value):

    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = tag_tuple

    if tag_comparison == "storage-expression":
        # TODO this just checks the value endswith the value from where it has a tag referencing, but really we should check for a complete
        # text match e.g. "All assets stored in environment variables"
        storage_location_value = callback_config.get("storage_location_value")
        if match.equals(storage_location_value, compare_to_value):
            if match.endswith(compare_value, compare_to_value):
                return True

    return False

def template_reference_callback(callback_config, tag_comparison, compare_value, compare_to_key, compare_to_value):

    return False

def verify(common_config:dict, verifier_config:dict, model:dict, template_model:dict) -> list:

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

    # Get a list of in-scope components
    in_scope_components = []
    components_key, components_data = find.key_with_tag(model, common_config["component-tags"]["component-data-tag"])
    for component_row in components_data:
        component_row_id_key, component_row_id_data = find.key_with_tag(component_row, "row-identifier")
        in_scope_key, in_scope_data = find.key_with_tag(component_row, common_config["component-tags"]["component-in-scope-tag"])
        if match.equals(in_scope_data, common_config["component-tags"]["component-in-scope-value"]):
            in_scope_components.append(component_row_id_data)

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
                    matching_component = match.get_equals(storage_location_value, [component_name for (_, component_name) in threat_component_entries])
                    if match.equals(matching_component, in_scope_components):
                        matching_in_scope_component = matching_component
                    else:
                        matching_in_scope_component = None

                    for threat_asset_entry_key, threat_asset_entry_value in threat_asset_entries:

                        if matching_in_scope_component is not None:
                            # Scenario A, B, C
                            # Then the asset can match on name or type, but the storage location must match the component
                            if reference.check_reference_row(asset, "ref", threat_asset_entry_key, threat_asset_entry_value, None, None) is not None and match.equals(matching_in_scope_component, storage_location_value):
                                if entry not in covering_threats:
                                    covering_threats.append(entry)
                        else:
                            # Scenario D
                            # The asset can only match on grouped storage type e.g. All assets stored in env vars
                            callback_config = {"storage_location_value":storage_location_value}
                            if reference.check_reference_row(asset, "ref", threat_asset_entry_key, threat_asset_entry_value, doc_reference_callback, callback_config) is not None:
                                if entry not in covering_threats:
                                    covering_threats.append(entry)

                if len(covering_threats) == 0:
                    issue_dict = {}
                    issue_dict["issue_key"] = row_id_key
                    issue_dict["issue_value"] = row_id_data
                    issue_dict["issue_table"] = threats_and_controls_key.getProperty("section")
                    issue_dict["issue_table_row"] = None    # Disable showing this in the error message
                    issue_dict["fixdata"] = common_config["grouped-text"]["start-assets-grouped-by-storage"]
                    # Need to get some helpful texts relating to the threats and control data
                    # Although we found the issue by looping over asset keys, the problem is in the threats and controls data
                    issue_dict["storage_location"] = storage_location_value
                    issue_dict["threats_and_controls_table"] = threats_and_controls_key.getProperty("section")
                    
                    if len(threats_and_controls_data) > 0:
                        threat_asset_entries = find.keys_with_tag(threats_and_controls_data[0], common_config["threat-tags"]["threat-asset-tag"])
                        issue_dict["asset_key"] = threat_asset_entries[0][0]
                    else:
                        issue_dict["asset_key"] = "undefined"

                    verify_return_list.append(VerifierIssue("no-covering-threat", "no-covering-threat-fix", issue_dict, ErrorType.NOT_SET))
            
                else:
                    # Store covering threats
                    storage_location_key.addProperty("covering-threats", covering_threats)

    return verify_return_list
