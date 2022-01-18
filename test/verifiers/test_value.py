#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import field_validation_value
from pprint import pprint

def get_value_config():
    
    config_yaml =   """
                    validator-config:
                        validator-dispatch-yaml-path:
                        validator-config-yaml-path:
                    not-mandatory-tag: "not-mandatory"  
                    tags:
                      - tag: validate-as-version
                      - tag: validate-as-date
                      - tag: validate-as-yes-no
                      - tag: validate-from-template
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_value(example_threat_model):

    config = get_value_config()

    output_list = field_validation_value.verify(config, example_threat_model, example_threat_model)

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 0

def test_value_bad_version(example_threat_model):

    config = get_value_config()

    example_threat_model["model-details"]["current-version"] = "abc"

    output_list = field_validation_value.verify(config, example_threat_model, example_threat_model)

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 1