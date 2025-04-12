#!/usr/bin/env python3

import pytest
import threatware.utils.load_yaml
from threatware.utils.error import ThreatwareError

def test_no_file():
    with pytest.raises(ThreatwareError):
        utils.load_yaml.yaml_file_to_dict("")
