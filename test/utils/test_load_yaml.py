#!/usr/bin/env python3

import pytest
import utils.load_yaml
from utils.error import ThreatwareError

def test_no_file():
    with pytest.raises(ThreatwareError):
        utils.load_yaml.yaml_file_to_dict("")
