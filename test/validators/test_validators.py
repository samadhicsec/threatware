#!/usr/bin/env python3

import pytest
from pathlib import Path
from validators.validators import Validator
from data.key import key as Key

def _get_validator():
    validator_config = {"validator-dispatch-yaml-path":str(Path(__file__).absolute().parent.joinpath("validators.yaml")),
                        "validator-config-yaml-path":str(Path(__file__).absolute().parent.joinpath("validator_config.yaml"))}

    return Validator(validator_config)

def test_validators():

    validator = _get_validator()

    output = validator.validate("validate-as-test", Key("test"), "test", {})

    assert output.result == True and output.validator_tag == "validate-as-test" and output.validator_name == "test_validator" \
        and output.validator_module == "test.validators.test_validator" and output.description == "output"

def test_validators_no_tag():

    validator = _get_validator()

    validator_tag = "does not exist"

    output = validator.validate(validator_tag, Key("test"), "test", {})

    assert output.result == False and output.error == f"No validator tag '{validator_tag}' is configured"

def test_validators_no_validator_key():

    validator = _get_validator()

    validator_tag = "validate-as-bad-test"

    output = validator.validate(validator_tag, Key("test"), "test", {})

    assert output.result == False and output.error == f"No 'validator' key is configured for '{validator_tag}'"

def test_validators_no_validator_configured():

    validator = _get_validator()

    validator_tag = "validate-as-no-validator-test"

    output = validator.validate(validator_tag, Key("test"), "test", {})

    assert output.result == False and output.error == f"No validator called 'does_not_exist' is configured"