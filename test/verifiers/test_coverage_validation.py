#!/usr/bin/env python3

import pytest
from ruamel.yaml import YAML
from verifiers import coverage_validation

def get_coverage_validation_config():

    config_yaml =   """
                    error-texts: 
                        no-covering-threat: "No threat was found for asset '{}'"
                    grouped-text: 
                    start-assets-grouped-by-storage: 
                        - "All assets stored"
                    all-assets:
                        - "All assets"
                    """    
    
    yaml=YAML(typ='safe')
    return yaml.load(config_yaml)

def test_asset_threat_coverage(example_threat_model):

    config = get_coverage_validation_config()

    output_list = coverage_validation.verify(config, example_threat_model, {})

    for error in output_list:
        print(f"{error.verifier}, {error.description}, {error.errortype}, {error.section}, {error.entry}")

    assert len(output_list) == 0

    # Need to check covering_threats have been successfully gathered as well


#@pytest.mark.parametrize("verifiers_to_load_list, expected_result", [
#    ([], {})
#])
#def test_load_verifiers(verifiers_to_load_list, expected_result):
#    assert load_verifiers(verifiers_to_load_list) == expected_result

#def test_load_verifiers_example():
#    load_list = ["example"]
#    output = load_verifiers(load_list)

#    assert "example" in output
#    assert output["example"]() == None