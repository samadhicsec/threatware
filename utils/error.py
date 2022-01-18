#!/usr/bin/env python3
"""
Custom Exception
"""

class ThreatwareError(Exception):
    pass

class ValidatorsError(ThreatwareError):
    pass