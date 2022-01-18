#!/usr/bin/env python3

import pytest
import json

import actions.verify as verify

def test_verify(example_threat_model):

    scheme = {}

    issues = verify.verify(scheme, example_threat_model, example_threat_model)

    #print(json.dumps(json_output, indent=4))

    assert len(issues) == 0