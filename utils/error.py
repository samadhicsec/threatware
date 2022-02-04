#!/usr/bin/env python3
"""
Custom Exception
"""

class ThreatwareError(Exception):
    pass

class ValidatorsError(ThreatwareError):
    pass

class ManageError(ThreatwareError):

    def __init__(self, text_key:str, template_values:dict, *args: object) -> None:
        self.text_key = text_key
        self.template_values = template_values
        super().__init__(*args)