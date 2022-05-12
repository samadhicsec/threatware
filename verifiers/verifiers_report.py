#!/usr/bin/env python3
"""
Reports on verifier output
"""

import logging
import jsonpickle
from utils.load_yaml import yaml_register_class
from verifiers.verifiers_config import VerifiersConfig

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class VerifiersReport:
    """ Produces a report on the output of the verification action

    """

    def __init__(self, config:VerifiersConfig, display_asset_coverage:bool = True, display_control_coverage:bool = True):
        yaml_register_class(VerifiersReport)

        self.config = config
        self.display_asset_coverage = display_asset_coverage
        self.display_control_coverage = display_control_coverage

    def report(self, verifier_issues_list:list, covered_assets_list:list) -> dict:
        self.verifier_issues_list = verifier_issues_list
        self.covered_assets_list = covered_assets_list

        self.control_coverage = {}
        # Generate the control coverage report consistaing of control, asset storage
        for covered_asset in self.covered_assets_list:
            # Loop through the controls
            for covered_threat in covered_asset.covering_threats:
                for control_key, control_value in covered_threat.threat_controls:
                    if control_value not in self.control_coverage:
                        self.control_coverage[control_value] = {}
                    if covered_asset.storage_location_value not in self.control_coverage[control_value]:
                        self.control_coverage[control_value][covered_asset.storage_location_value] = []
                    if covered_asset.asset_value not in self.control_coverage[control_value][covered_asset.storage_location_value]:
                        self.control_coverage[control_value][covered_asset.storage_location_value].append(covered_asset.asset_value)

    def _get_state(self):

        def _covered_assets_sort(value):
            return len(value.covering_threats)

        output = {}
        output['issues'] = self.verifier_issues_list
        if self.display_asset_coverage:
            output['asset-coverage-report'] = sorted(self.covered_assets_list, key=_covered_assets_sort)
        if self.display_control_coverage:
            control_report = []
            for control, asset_list in self.control_coverage.items():
                control_report_entry = {}
                control_report_entry["control"] = control
                control_report_entry["locations"] = []
                for location, asset_list in asset_list.items():
                    location_report_entry = {}
                    location_report_entry["location"] = location
                    location_report_entry["assets"] = asset_list
                    control_report_entry["locations"].append(location_report_entry)
                control_report.append(control_report_entry)    
            output['control-coverage-report'] = control_report
            #output['control-coverage-report'] = self.control_coverage
        return output

    def __getstate__(self):
        """ Used by jsonpickle to state of class to output """
        return self._get_state()

    def tojson(self):
        return jsonpickle.encode(self, unpicklable=False)

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(node._get_state())