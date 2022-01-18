#!/usr/bin/env python3
"""
Class ValidatorOutput
"""

class ValidatorOutput:
    """
    Holds the output of a validator and is used to format output of validator
    """

    def __init__(self, validator_tag:str = None, validator_name:str = None, validator_module:str = None, result:bool = False, description:str = None, error:str = None):
        """
        Create a ValidatorOutput object

        Parameters
        ----------
        validator_tag : str
            The tag that will be looked up in the validator config YAML to get the validator method and config to use
        validator_name : str
            The name of the validator
        validator_module : str
            The module where the validator was laded from
        result : bool
            True if validation was succeeded, False otherwise (and in the case of error)
        description: str
            Description text about the resultof validation
        error: str
            Error text if the validator failed for some reason
        """

        self.validator_tag = validator_tag
        self.validator_name = validator_name
        self.validator_module = validator_module
        self.result = result
        self.description = description
        self.error = error

    # TODO: sort out the format of the validator error messages