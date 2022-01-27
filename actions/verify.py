#!/usr/bin/env python3
"""
Verify a threat model
"""

import logging
import jsonpickle
import pprint
from verifiers.verifiers_config import VerifiersConfig
from verifiers.threat_coverage import ThreatCoverage
from verifiers.verifiers_report import VerifiersReport
from verifiers.verifiers import Verifiers

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def config(scheme:dict):

    verifiers_config = scheme.get("verifiers", {})

    return VerifiersConfig(verifiers_config)

def verify(config:VerifiersConfig, threatmodel:dict, tm_template:dict):

    verifiers = Verifiers(config)

    issues = verifiers.verify(threatmodel, tm_template)
    #for issue in issues:
    #    print(issue)

    # Return issues
    return issues

def coverage(config:VerifiersConfig, threatmodel:dict):

    threat_coverage = ThreatCoverage(config)

    coverage = threat_coverage.coverage(threatmodel)

    return coverage

def report(config:VerifiersConfig, issues, coverage):

    verifiers_report = VerifiersReport(config)

    verifiers_report.report(issues, coverage)

    return verifiers_report

#def tojson(issues):

#    return jsonpickle.encode(issues, unpicklable=False)