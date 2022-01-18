#!/usr/bin/env python3

import pytest
from schemes.schemes import load_scheme
from utils.load_yaml import yaml_file_to_dict

@pytest.mark.parametrize("scheme, expected_result", [
    ("", "{}"),
    ("confluence_1.0", str(yaml_file_to_dict("schemes/confluence-scheme-1.0.yaml")["scheme"])),
])
def test_load_scheme(scheme, expected_result):
    assert str(load_scheme(scheme)) == expected_result
