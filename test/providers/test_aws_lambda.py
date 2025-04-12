#!/usr/bin/env python3

import pytest
import threatware.providers.aws_lambda as aws_lambda


@pytest.mark.parametrize("suggested_path, expected_result", [
    ("", "/tmp"),
    (".threatware", "/tmp/.threatware"),
])
def test_config_path_tmp(suggested_path, expected_result):
    assert aws_lambda.AWSLambdaContext({}).get_config_base_dir(suggested_path) == expected_result

