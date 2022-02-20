
#!/usr/bin/env python3
"""
Manage a threat model
"""


# We can tag fields with 'measure' or 'risk_analysis', and pass in a doc and a template, and compare values in these fields.  The template needn't be an actual template and could be any other TM, like a golden TM

import logging
import measure.measure_config as manage_config
from measure.measure_output import MeasureOutput
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def config(translator):

    return manage_config.config(translator)

def output(config:dict):

    return MeasureOutput(config.get("output", {}))

def distance(config:dict, output:MeasureOutput, doc_model:dict, ref_model:dict):

    pass

def distance_to_approved(config:dict, output:MeasureOutput, doc_model:dict):
    """ 
    Measure the distance of the passed in threat model to the approved version

    """

    # Get the ID of the TM from the model

    # Get the approved version from the index metadata

    # Get the approved version and hydrate it (not sure how to do this?)

    # Measure distance between two