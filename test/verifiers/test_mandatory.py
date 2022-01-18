#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import field_validation_mandatory

def get_field_validation_mandatory_config():

    config_yaml =   """
                    default: True
                    exceptions-tag: "not-mandatory"
                    error-texts:
                        missing-mandatory: "A value for the field '{}' is mandatory"
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_mandatory(example_threat_model):

    config = get_field_validation_mandatory_config()

    output_list = field_validation_mandatory.verify(config, example_threat_model, {})
    print(output_list)
    assert len(output_list) == 0

def test_mandatory_not_present(example_threat_model):

    config = get_field_validation_mandatory_config()

    # Set a mandatory value to empty
    example_threat_model["components"]["details"][0]["name"] = ""
    
    output_list = field_validation_mandatory.verify(config, example_threat_model, {})
    print(output_list)
    assert len(output_list) == 1

def test_mandatory_not_present_as_None(example_threat_model):

    config = get_field_validation_mandatory_config()

    # Set a mandatory value to empty
    example_threat_model["components"]["details"][1]["name"] = None
    
    output_list = field_validation_mandatory.verify(config, example_threat_model, {})
    print(output_list)
    assert len(output_list) == 1

def test_mandatory_not_mandatory(example_threat_model):

    config = get_field_validation_mandatory_config()

    # Set a mandatory value to empty
    detail0 = example_threat_model["components"]["details"][0]
    detail0["in-scope"] = ""
    for key_entry, _ in detail0.items():
        if key_entry == "in-scope":
            key_entry.addTag("not-mandatory")
            break
    
    output_list = field_validation_mandatory.verify(config, example_threat_model, {})
    print(output_list)
    assert len(output_list) == 0
