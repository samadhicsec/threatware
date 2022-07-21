#!/usr/bin/env python3
"""
Verify a threat model
"""

import logging
from utils.error import VerifyError
from language.translate import Translate
from utils.output import FormatOutput
from utils import match
from verifiers.verifiers_config import VerifiersConfig
from verifiers.threat_coverage import ThreatCoverage
from verifiers.verifiers_report import VerifiersReport
from verifiers.verifiers import Verifiers

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def config(scheme:dict):

    verifiers_config = scheme.get("verifiers", {})

    return VerifiersConfig(verifiers_config)


def assign_default_tags(config:VerifiersConfig, model:dict):
    """
    Utility method to populate a model with the default verify tags.
    """
    verifiers = Verifiers(config)

    verifiers.assign_key_tags(model)


def verify(config:VerifiersConfig, threatmodel:dict, tm_template:dict):

    logger.info("Entering verify")

    output = FormatOutput(config.verifiers_config_dict.get("output"))

    try: 
        verifiers = Verifiers(config)

        issues = verifiers.verify(threatmodel, tm_template)

        if len(issues) == 0:
            output.setSuccess("success-no-issues", {}, issues)
        elif len([issue for issue in issues if issue.isError()]) > 0:
            output.setInformation("error-issues", {}, issues)
        else:
            output.setInformation("warn-info-issues", {}, issues)

    except VerifyError as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting verify")

    return output

def _coverage(config:VerifiersConfig, threatmodel:dict):

    threat_coverage = ThreatCoverage(config)

    coverage = threat_coverage.coverage(threatmodel)

    return coverage

def _reports_to_show(reports_parameter:str):
    """ Returns a bool 2-tuple indicating if the asset and control reports should be shown """

    if match.is_empty(reports_parameter):
        return False, False

    if reports_parameter == "none":
        return False, False
    elif reports_parameter == "assets":
        return True, False
    elif reports_parameter == "controls":
        return False, True
    elif reports_parameter == "all":
        return True, True

    logger.warning(f"Unrecognised value '{reports_parameter}' for 'reports' parameter.  Using default.")
    return False, False

def report(config:VerifiersConfig, threatmodel:dict, issues:list, verify_reports:str):

    logger.info("Entering report")

    output = FormatOutput(config.verifiers_config_dict.get("output"))

    try:
        
        coverage = _coverage(config, threatmodel)

        show_asset_report, show_control_report = _reports_to_show(verify_reports)

        verifiers_report = VerifiersReport(config, show_asset_report, show_control_report)

        verifiers_report.report(issues, coverage)

        if len(issues) == 0:
            output.setSuccess("success-no-issues", {}, verifiers_report)
        elif len([issue for issue in issues if issue.isError()]) > 0:
            output.setInformation("error-issues", {}, verifiers_report)
        else:
            output.setInformation("warn-info-issues", {}, verifiers_report)        

    except VerifyError as error:
        output.setError(error.text_key, error.template_values)

    logger.info("Exiting report")

    return output
