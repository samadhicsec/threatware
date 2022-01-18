import pytest
import validators.regex
from data.key import key as Key

def test_valid_regex():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"regex"}

    test_key = Key("test-key")
    config["pattern"] = "(?i)yes|no"
    valid_value = "yes"

    result = validators.regex.validate(config, test_key, valid_value, references)
    
    property_text = test_key.getProperty(references['validator-tag'])

    assert result == True
    assert property_text == config["output_text_valid"].format(test_key, valid_value, config["pattern"])
    

def test_invalid_regex():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"regex"}

    test_key = Key("test-key")
    config["pattern"] = "(?i)yes|no"
    valid_value = "purple"

    result = validators.regex.validate(config, test_key, valid_value, references)

    property_text = test_key.getProperty(references['validator-tag'])

    assert result == False
    assert property_text == config["output_text_invalid"].format(test_key, valid_value, config["pattern"])

def test_invalid_regex_no_pattern():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"regex"}

    test_key = Key("test-key")
    # Testing for failure due to no pattern
    #config["pattern"] = "(?i)yes|no"
    valid_value = "yes"

    result = validators.regex.validate(config, test_key, valid_value, references)

    assert result == False

def test_invalid_regex_invalid_pattern():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    references = {'validator-tag':"regex"}

    test_key = Key("test-key")
    # Testing for failure due to no pattern
    config["pattern"] = "\\"
    valid_value = "yes"

    result = validators.regex.validate(config, test_key, valid_value, references)

    assert result == False