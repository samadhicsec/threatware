#!/usr/bin/env python3
"""
Reports on threats covering assets in location
"""

import logging
from utils import match
from utils.load_yaml import yaml_register_class
from verifiers.verifiers_config import VerifiersConfig
from data import find
from data import key as Key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class CoveringThreat:

    def __init__(self, threat_description:str, threat_controls:list):
        yaml_register_class(CoveringThreat)

        self.threat_description = threat_description
        self.threat_controls = threat_controls

    def _get_state(self):

        output = {}
        output['threat_description'] = self.threat_description
        output['controls'] = []
        for control_key, control_value in self.threat_controls:
            output['controls'].append(control_value)
        
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())

class CoveredAsset:

    def __init__(self, asset:Key, asset_value:str, storage_location:Key, storage_location_value:str, covering_threats:list):
        yaml_register_class(CoveredAsset)

        self.asset = asset
        self.asset_value = asset_value
        self.storage_location = storage_location
        self.storage_location_value = storage_location_value
        self.covering_threats = covering_threats

    def _get_state(self):

        output = {}
        output['asset'] = self.asset_value
        output['storage-location'] = self.storage_location_value
        output['covering-threats'] = self.covering_threats
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()
        
    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())


class ThreatCoverage:
    """ Searches a model for existing information regarding the threats covering assets in locations

    """

    def __init__(self, config:VerifiersConfig):
        self.config = config

    def coverage(self, model:dict) -> list:

        covered_assets = []

        common_config = self.config.verifiers_config_dict["common"]

        # Get a list of out-of-scope components
        out_of_scope_components = []
        components_key, components_data = find.key_with_tag(model, common_config["component-tags"]["component-data-tag"])
        for component_row in components_data:
            component_row_id_key, component_row_id_data = find.key_with_tag(component_row, "row-identifier")
            in_scope_key, in_scope_data = find.key_with_tag(component_row, common_config["component-tags"]["component-in-scope-tag"])
            if not match.equals(in_scope_data, common_config["component-tags"]["component-in-scope-value"]):
                out_of_scope_components.append(component_row_id_data)

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

                    if storage_location_value in out_of_scope_components:
                        logger.debug(f"Ignoring coverage report on asset '{row_id_key.name}' in storage location '{storage_location_value}' as '{storage_location_value}' is out of scope")
                        continue

                    if storage_location_key.getProperty("excluded"):    # Returns None (evals to False) if not present, otherwise returns True/False
                        logger.debug(f"Ignoring coverage report on asset '{row_id_key.name}' in storage location '{storage_location_value}' it has a tag that excludes it")
                        continue

                    covering_threats = storage_location_key.getProperty("covering-threats")

                    covering_threats_list = []
                    if covering_threats is not None:
                        # Get required information about threat
                        for threat in covering_threats:

                            threat_description = find.key_with_tag(threat, common_config["threat-tags"]["threat-description-tag"])[1]
                            threat_controls = find.keys_with_tag(threat, common_config["threat-tags"]["threat-control-tag"])

                            covering_threats_list.append(CoveringThreat(threat_description, threat_controls))

                    covered_assets.append(CoveredAsset(row_id_key, row_id_data, storage_location_key, storage_location_value, covering_threats_list))

        return covered_assets