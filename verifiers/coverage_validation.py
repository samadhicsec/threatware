#!/usr/bin/env python3
"""
Verifies that all assets are covered by a threat
"""
from data import find
import logging
import verifiers.reference as reference
from verifiers.verifier_error import ErrorType
from verifiers.verifier_error import VerifierError
from utils import match
from utils import keymaster

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


#def _get_ref_tag_parts(reftag:str):

    # Split tag into parts
#    tag_parts = reftag.split("/")
#    tag_prefix = tag_parts[0]
#    tag_data_tag_name = tag_parts[1]
#    tag_field_tag_name = tag_parts[2]
#    tag_comparison = "equals"
#    if len(tag_parts) == 4:
#        tag_comparison = tag_parts[3]

#    return tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison

#def _valid_storage_expression(verifier_config, compare_to_value, compare_value):

#    # Check if it's an expression that is independent of a value
#    if match.equals(compare_to_value, verifier_config["grouped-text"]["all-assets"]):
#        return True
#    if match.starts_ends(compare_to_value, verifier_config["grouped-text"]["start-assets-grouped-by-storage"], compare_value):
#        return True

#    return False

#def _check_tag_comparison(verifier_config, tag_comparison, compare_to_value, compare_value):

#    if tag_comparison == "endswith":
#        if match.endswith(compare_to_value, compare_value):
#            return True
#    elif tag_comparison == "storage-expression":
#        return _valid_storage_expression(verifier_config, compare_to_value, compare_value)
#    else:
#        if match.equals(compare_to_value, compare_value):
#            return True

#    return False

#def _check_reference(verifier_config, ref_tag, asset, asset_data_tag, threat_asset_entry_value):

#    if not ref_tag.startswith("ref/"):
        # We are only looking at reference tags
#        return False

#    tag_prefix, tag_data_tag_name, tag_field_tag_name, tag_comparison = _get_ref_tag_parts(ref_tag)

#    if tag_data_tag_name != asset_data_tag:
#        return False

#    found_key, found_value = find.key_with_tag(asset, tag_field_tag_name)

#    if found_key is None:
#        return False

#    return _check_tag_comparison(verifier_config, tag_comparison, found_value, threat_asset_entry_value)
    
def doc_reference_callback(callback_config, tag_comparison, compare_value, compare_to_key, compare_to_value):

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

def verify(verifier_config:dict, model:dict, template_model:dict) -> list:

    verify_return_list = []

    verifier_name = __file__.split(".")[0]

    # Get a reference to all the possible error messages that can be returned
    errorTexts = verifier_config["error-texts"]

    # Get all the data required to do the validation
    tagged_asset_data_list = verifier_config["asset-data-tag"]
    all_assets = []
    for tag in tagged_asset_data_list:
        tag_asset_data_key, tag_asset_data_value = find.key_with_tag(model, tag)
        if not isinstance(tag_asset_data_value, list):
            logger.error(f"Expecting the data tagged with '{tag}' to be a list, but it was a '{type(tag_asset_data_value)}'. Ignoring.")
            continue
    
        all_assets.append((tag, tag_asset_data_key, tag_asset_data_value))

    if len(all_assets) == 0:
        logger.error(f"Could not find any asset data tagged with '{verifier_config['asset-data-tag']}'")

    threats_and_controls_key, threats_and_controls_data = find.key_with_tag(model, verifier_config["threats-data-tag"])
    if threats_and_controls_data is None:
        logger.error(f"Could not find threat data tagged with '{verifier_config['threats-data-tag']}'")

    # Get a list of in-scope components
    in_scope_components = []
    components_key, components_data = find.key_with_tag(model, verifier_config["component-data-tag"])
    for component_row in components_data:
        component_row_id_key, component_row_id_data = find.key_with_tag(component_row, "row-identifier")
        in_scope_key, in_scope_data = find.key_with_tag(component_row, verifier_config["component-in-scope-tag"])
        if match.equals(in_scope_data, verifier_config["component-in-scope-value"]):
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
            for storage_location_key, storage_location_value in find.keys_with_tag(asset, verifier_config['asset-location-tag']):

                logger.debug(f"Checking threat coverage for asset '{row_id_key.name}' in storage location '{storage_location_value}'")

                # Add an empty list of covering threats.  The list will be appended to as it is found.
                covering_threats = []
                row_id_key.addProperty(storage_location_key, covering_threats)

                # An asset is covered by a threat when:
                # Scenario A: threat component includes = in-scope asset storage location AND asset = name
                # Scenario B: threat component includes = in-scope asset storage location AND asset = type
                # Scenario C: threat component includes = in-scope asset storage location AND asset = all assets in component
                # Scenario D: threat component is anything AND asset = all assets in known storage type (e.g. env var)
                
                for entry in threats_and_controls_data:

                    # An entry in the threats data section can contain multiple assets and components
                    
                    # Note, we are just searching the threats row here, so the assets and components returned will be in the same table row
                    threat_asset_entries = find.keys_with_tag(entry, verifier_config["threat-asset-tag"])
                    threat_component_entries = find.keys_with_tag(entry, verifier_config["threat-component-tag"])

                    if len(threat_asset_entries) == 0:
                        # This validation issue will be raised elsewhere
                        continue

                    # Does the storage location for the asset match one of the components?
                    matching_component = match.get_equals(storage_location_value, [component_name for (_, component_name) in threat_component_entries])
                    if match.equals(matching_component, in_scope_components):
                        matching_in_scope_component = matching_component
                    else:
                        matching_in_scope_component = None
                    # if matching_component is not None
                    # Scenario A, B, C
                    # This confirms 'threat component includes = in-scope asset storage location' 
                    
                    #matching_storage_type = None
                    #if matching_component is None:
                        # Checking Scenario D
                    #    template_tag_asset_data_key, template_tag_asset_data_value = find.key_with_tag(template_model, asset_data_tag)
                    #    if (preApproved_storage_types := template_tag_asset_data_key.getProperty("preApproved")) is not None:
                    #        matching_storage_type = match.get_equals(storage_location_value, preApproved_storage_types)
                            # If this is not None, then Scenario D could still be viable, but we need to check the threat text referencing this value

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

                    #for asset_entry_key_tag in threat_asset_entries[0][0].getTags():
                        # All these keys have the same set of tags, so we just use the first key to get the tags
                    #    for threat_asset_entry_key, threat_asset_entry_value in threat_asset_entries:

                    #        if matching_component is not None:
                                # Scenario A, B, C
                                # Then the asset can match on name or type, but the storage location must match the component
                                
                                # Does the reference tag extract a value from the asset, that matches the asset covered by this threat
                    #            if _check_reference(verifier_config, asset_entry_key_tag, asset, asset_data_tag, threat_asset_entry_value):
                    #                if entry not in covering_threats:
                    #                    covering_threats.append(entry)

                    #        elif matching_storage_type is not None:
                                # Scenario D
                                # The asset can only match on grouped storage type e.g. All assets stored in env vars
                                # Storage types come from the template

                                # for trefs lookup key tags and get keys.  The validate key values against the tags on the key, any that don't validate are storage types we want to support i.e. storage locations added to the template
                                # Probably need to do this centrally and pass it in, so we don't do it in lots of places. Actually could just do once in a helper method and cache
                    #            a = 1
                                # TODO is it sufficient to just check if the storage type of asset matches a "all asset" version of text for this threat row?
                                # otherwise, template preApproved values should have a property marking them so.
                                # Problem: Need to take the threat asset value e.g. "All assets stored as env var", and the asset storage location e.g. env vars, component 1, etc. and check when the threat asset value covers the storage location
                                # Solution
                                # - check the storage location is a preapproved storage type (need to store list against data section)
                                # - check the threat asset value ends in the storage type
                                # - better - check the threat asset value starts with the group text.
                                # - better - check that the current threat tag references a valid value from the template


                if len(covering_threats) == 0:
                    verify_return_list.append(VerifierError(verifier_config, 
                                                            verifier_name,
                                                            errorTexts["no-covering-threat"].format(row_id_data, storage_location_value), 
                                                            None, 
                                                            ErrorType.NOT_SET, 
                                                            keymaster.get_section_for_key(threats_and_controls_key), 
                                                            None))
            
            # TODO: If covering threats found return as analysis object.

    return verify_return_list


#def verify_old(verifier_config:dict, model:dict, template_model:dict) -> list:

#    verify_return_list = []

#    verifier_name = __file__.split(".")[0]

    # Get a reference to all the possible error messages that can be returned
#    errorTexts = verifier_config["error-texts"]
    # Get a reference to all grouped asset texts
#    groupedAssets = verifier_config["grouped-text"]

    # Get all the data required to do the validation
    #components_key, components_data = find.key_with_tag(model, "components-data")
#    functional_asset_key, functional_asset_data = find.key_with_tag(model, "functional-asset-data")
#    technical_asset_key, technical_asset_data = find.key_with_tag(model, "technical-asset-data")
#    threats_and_controls_key, threats_and_controls_data = find.key_with_tag(model, "threats-and-controls-data")
#    if threats_and_controls_data is None:
#        logger.error(f"Could not find a 'threats-and-controls-data' tagged data")


#    if not isinstance(functional_asset_data, list) or not isinstance(technical_asset_data, list):
#        logger.error(f"Expecting the both the Functional Assets (a '{type(functional_asset_data)}') and Technical Assets (a '{type(technical_asset_data)}') tables to be lists")
    
#    all_assets = functional_asset_data + technical_asset_data

    # Loop through the assets
#    for asset in all_assets:

        # Get the row identifier (from verifier config)
#        row_id_key, row_id_data = find.key_with_tag(asset, "row-identifier")
#        if row_id_key is None:
#            logger.error(f"Could not find a 'row-identifier' field for asset '{asset}'")
        
        # TODO make this more generic by using ther 'ref/' tags from the threats-and-controls-data asset-name-tag, and see if any of them match
        # the values of the particular asset row we are looking at.  Coverage validation is the reverse of reference validation - so wouldn't it
        # be easier to run reference validation and set a property on all the all the successfully referenced assets, so those without the reference
        # must not be covered by a threat?

        # Is this asset covered by a threat...

        # ... either by name, type or storage location ...
#        asset_key, asset_name = find.key_with_tag(asset, verifier_config["asset-name-tag"])
#        if asset_key is None:
#            logger.error(f"Could not find a '{verifier_config['asset-name-tag']}' tagged key for asset '{asset}'")
#            continue
#        asset_key, asset_type = find.key_with_tag(asset, verifier_config['asset-type-tag'])
#        if asset_key is None:
#            logger.warning(f"Could not find a '{verifier_config['asset-type-tag']}' tagged key for asset '{asset}'")
        
#        asset_storage_locations_list = find.keys_with_tag(asset, verifier_config['storage-location-tag'])
#        if len(asset_storage_locations_list)  == 0:
#            logger.warning(f"Could not find any '{verifier_config['storage-location-tag']}' tagged keys for asset '{asset}'")

#        logger.debug(f"Checking threat coverage for {asset_name}")
        #print(f"Checking threat coverage for {asset_name}")

        # Add an empty list of covering threats.  The list will be appended to as it is found.
#        covering_threats = []
#        asset_key.addProperty(verifier_name, covering_threats)

        
#        for entry in threats_and_controls_data:

            # ... that directly references its name
#            for (_, threat_asset_name) in find.keys_with_tag_matching_regex(entry, "^ref/.*/" + verifier_config["asset-name-tag"] + "(/.*)?"):
#                if match.equals(threat_asset_name, asset_name):
                    # Record the threat that covers the asset
#                    if entry not in covering_threats:
#                        covering_threats.append(entry)

            # ... that references an asset type that this asset belongs to
#            for (_, threat_asset_type) in find.keys_with_tag(entry, "^ref/.*/" + verifier_config["asset-type-tag"] + "(/.*)?"):
#                if match.equals(threat_asset_type, asset_type):
                    # Record the threat that covers the asset
#                    if entry not in covering_threats:
#                        covering_threats.append(entry)

            # ... that references a storage location this asset is stored in
#            for (_, threat_asset_location) in find.keys_with_tag(entry, "^ref/.*/" + verifier_config['storage-location-tag'] + "(/.*)?"):
#                if match.starts_ends(threat_asset_location, groupedAssets["start-assets-grouped-by-storage"], asset_storage_locations_list):
                    # Record the threat that covers the asset
#                    if entry not in covering_threats:
#                        covering_threats.append(entry)
            

#        if len(covering_threats) == 0:
#            verify_return_list.append(VerifierError(verifier_config, 
#                                                    verifier_name,
#                                                    errorTexts["no-covering-threat"].format(row_id_data), 
#                                                    None, 
#                                                    ErrorType.NOT_SET, 
#                                                    threats_and_controls_key.getProperty("section"), 
#                                                    None))
        
        # If covering threats found return as analysis object

#    return verify_return_list