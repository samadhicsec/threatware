#!/usr/bin/env python3
"""
Verify a threat model
"""

import logging
import jsonpickle
import pprint
from verifiers.verifiers import Verifiers

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def verify(scheme:dict, threatmodel:dict, tm_template:dict):

    verifiers_config = scheme.get("verifiers", {})

    verifiers = Verifiers(verifiers_config)

    issues = verifiers.verify(threatmodel, tm_template)
    #for issue in issues:
    #    print(issue)

    # Return issues
    return issues

def tojson(issues):

    return jsonpickle.encode(issues, unpicklable=False)