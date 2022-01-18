import pytest
import validators.template
from data.key import key as Key

def test_valid_template():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}', template value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}', , template values {}"
    
    # If we read this key and value from a model
    test_key = Key("test-key", ["template-verification-test"])
    valid_value = "value from template"

    # And the same key and value exists in the template
    template_key = Key("test-key", ["template-verification-test"])
    template = {template_key:"value from template"}

    references = {}
    references['validator-tag'] = "template-verification-test"
    references['template-model'] = template

    # then validate should return True
    result = validators.template.validate(config, test_key, valid_value, references)
    
    property_text = test_key.getProperty(references['validator-tag'])

    assert result == True
    assert property_text == config["output_text_valid"].format(test_key, valid_value, template[template_key])

def test_invalid_template_invalid_value():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    
    # If we read this key and value from a model
    test_key = Key("test-key", ["template-verification-test"])
    invalid_value = "value not from template"

    # And the same key and value exists in the template
    template_key = Key("test-key", ["template-verification-test"])
    template = {template_key:"value from template"}

    references = {}
    references['validator-tag'] = "template-verification-test"
    references['template-model'] = template

    # then validate should return True
    result = validators.template.validate(config, test_key, invalid_value, references)
    
    property_text = test_key.getProperty(references['validator-tag'])

    assert result == False
    assert property_text == config["output_text_invalid"].format(test_key, invalid_value, [template[template_key]])

def test_invalid_template_invalid_key():

    config = {}
    config["output_text_valid"] = "Valid: Key '{}', value '{}'"
    config["output_text_invalid"] = "Invalid: Key '{}', value '{}'"
    
    # If we read this key and value from a model
    test_key = Key("different-test-key", ["template-verification-test"])
    valid_value = "value from template"

    # And the same key and value exists in the template
    template_key = Key("test-key", ["template-verification-test"])
    template = {template_key:"value from template"}

    references = {}
    references['validator-tag'] = "template-verification-test"
    references['template-model'] = template

    # then validate should return True
    result = validators.template.validate(config, test_key, valid_value, references)
    
    property_text = test_key.getProperty(references['validator-tag'])

    assert result == False
    assert property_text == config["output_text_invalid"].format(test_key, valid_value, [template[template_key]])
