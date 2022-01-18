#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import reference_validation
from pprint import pprint

def get_ref_val_config():

    config_yaml =   """
                    tag-prefix: "ref"
                    error-texts:
                        reference-not-found: "The field '{}' with value '{}' must match one of the following section/field name pairs - '{}'"
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_reference_validation(example_threat_model):

    config = get_ref_val_config()

    output_list = reference_validation.verify(config, example_threat_model, {})

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 0

def test_reference_validation_bad_component_ref(example_threat_model):

    config = get_ref_val_config()

    example_threat_model["components"]["access-control"][0]["component"] = "This is not a valid component name"
    print(f'{example_threat_model["components"]["access-control"][0]}')
    for key_entry, value_entry in example_threat_model["components"]["access-control"][0].items():
        print(f"key {key_entry} tags{key_entry.getTags()}")

    output_list = reference_validation.verify(config, example_threat_model, {})

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 1

def test_reference_validation_bad_component_ref2(example_threat_model):

    config = get_ref_val_config()

    example_threat_model["components"]["access-control"][0]["component"] = "This is not a valid component name"
    example_threat_model["components"]["access-control"][1]["component"] = "This is not a valid component name"
    
    output_list = reference_validation.verify(config, example_threat_model, {})

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 2