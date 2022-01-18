#!/usr/bin/env python3

import pytest
import validators.date
from data.key import key as Key

def test_valid_date():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"validate-as-date"}

    valid_date = "2021-01-01"

    result = validators.date.validate(config, Key("test-key"), valid_date, references)

    assert result == True

def test_valid_date_property():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"validate-as-date"}

    valid_date = "2021-01-01"

    test_key = Key("test-key")

    result = validators.date.validate(config, test_key, valid_date, references)

    property_text = test_key.getProperty(references['validator-tag'])

    assert property_text == config["output_text_valid"].format(test_key, valid_date)

def test_invalid_date():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"    
    references = {'validator-tag':"validate-as-date"}

    invalid_date = "abc"

    result = validators.date.validate(config, Key("test-key"), invalid_date, references)

    assert result == False

def test_invalid_date_property():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"validate-as-date"}

    valid_date = "abc"

    test_key = Key("test-key")

    result = validators.date.validate(config, test_key, valid_date, references)

    property_text = test_key.getProperty(references['validator-tag'])

    assert property_text == config["output_text_invalid"].format(test_key, valid_date)

def test_invalid_no_date():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"    
    references = {'validator-tag':"validate-as-date"}

    invalid_date = ""

    result = validators.date.validate(config, Key("test-key"), invalid_date, references)

    assert result == False