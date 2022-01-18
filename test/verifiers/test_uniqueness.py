#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import field_validation_uniqueness
from pprint import pprint

def get_uniqueness_config():
    
    config_yaml =   """
                    error-texts:
                        document-unique: "The value '{}' in field '{}' must be unique in the document amongst the following section/field name pairs - {}.
                        Duplicate value(s) were found in the following section/field name pairs - {}"
                    tags:
                        - tag: document-unique
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_uniqueness(example_threat_model):

    config = get_uniqueness_config()

    output_list = field_validation_uniqueness.verify(config, example_threat_model, {})

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 0

def test_uniqueness_one_duplicate(example_threat_model):

    config = get_uniqueness_config()

    # Set a mandatory value to empty
    example_threat_model["components"]["details"][0]["name"] = example_threat_model["components"]["details"][1]["name"]
    
    output_list = field_validation_uniqueness.verify(config, example_threat_model, {})
    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")
    assert len(output_list) == 1

def test_uniqueness_many_duplicates(example_threat_model):

    config = get_uniqueness_config()

    # Set a mandatory value to empty
    example_threat_model["components"]["details"][0]["name"] = example_threat_model["assets"]["technical"][1]["name"]
    example_threat_model["assets"]["functional"][0]["name"] = example_threat_model["assets"]["technical"][1]["name"]
    example_threat_model["assets"]["functional"][1]["name"] = example_threat_model["assets"]["technical"][1]["name"]
    example_threat_model["assets"]["technical"][0]["name"] = example_threat_model["assets"]["technical"][1]["name"]
    example_threat_model["assets"]["technical"][1]["name"] = example_threat_model["assets"]["technical"][1]["name"]
    
    output_list = field_validation_uniqueness.verify(config, example_threat_model, {})
    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")
    assert len(output_list) == 1