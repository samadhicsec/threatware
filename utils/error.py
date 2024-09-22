#!/usr/bin/env python3
"""
Custom Exception
"""

class ThreatwareError(Exception):

    def __init__(self, text_key:str = "", template_values:dict = {}, *args: object) -> None:
        self.text_key = "internal-error"
        if text_key is not None and len(text_key.strip()) > 0:
            self.text_key = text_key
        self.template_values = template_values
        super().__init__(*args)

class SchemeError(ThreatwareError):
    pass

class ConvertError(ThreatwareError):
    pass

class ProviderError(ConvertError):
    pass

class ValidatorsError(ThreatwareError):
    pass

class VerifyError(ThreatwareError):
    pass

class ManageError(ThreatwareError):
    pass
    # def __init__(self, text_key:str, template_values:dict, *args: object) -> None:
    #     self.text_key = text_key
    #     self.template_values = template_values
    #     super().__init__(*args)

class MeasureError(ThreatwareError):
    pass
    # def __init__(self, text_key:str, template_values:dict, *args: object) -> None:
    #     self.text_key = text_key
    #     self.template_values = template_values
    #     super().__init__(*args)

class StorageError(ThreatwareError):
    pass
    # def __init__(self, text_key:str, template_values:dict, *args: object) -> None:
    #     self.text_key = text_key
    #     self.template_values = template_values
    #     super().__init__(*args)