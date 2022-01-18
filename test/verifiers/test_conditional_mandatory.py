#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import field_validation_conditional_mandatory

def get_field_validation_conditional_mandatory_config():

    config_yaml =   """
                    error-texts:
                        missing-conditional-mandatory: "The value for the field '{}' is '{}', so a value for the field '{}' is mandatory"
                    tags:
                        # The following pairs of tag define a tag that is mandatory if another tag has a value
                        - tag: "tech-stack"
                          depends-on: "in-scope"
                          depends-on-value: "Yes"
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_conditional_mandatory(example_threat_model):

    config = get_field_validation_conditional_mandatory_config()

    output_list = field_validation_conditional_mandatory.verify(config, example_threat_model, {})
    
    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")
    
    assert len(output_list) == 0

def test_conditional_mandatory_not_set(example_threat_model):

    config = get_field_validation_conditional_mandatory_config()
    
    example_threat_model["components"]["details"][0]["tech-stack"] = None

    output_list = field_validation_conditional_mandatory.verify(config, example_threat_model, {})
    
    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")
    
    assert len(output_list) == 1