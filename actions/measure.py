
#!/usr/bin/env python3
"""
Measure a threat model
"""


# We can tag fields with 'measure' or 'risk_analysis', and pass in a doc and a template, and compare values in these fields.  The template needn't be an actual template and could be any other TM, like a golden TM

import logging
import measure.measure_config as measure_config
import measure.measure_distance as measure_distance
from measure.measure_output import MeasureOutput
from utils.model import assign_row_identifiers, assign_parent_keys
import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


def config():

    return measure_config.config()

def _output(config:dict):

    return MeasureOutput(config.get("output", {}))

def distance(config:dict, doc_model:dict, ref_model:dict):

    output = _output(config)

    assign_row_identifiers(doc_model)
    assign_parent_keys(doc_model)
    assign_row_identifiers(ref_model)
    assign_parent_keys(ref_model)

    return measure_distance.distances(config, output, doc_model, ref_model)

def distance_to_approved(config:dict, output:MeasureOutput, doc_model:dict):
    """ 
    Measure the distance of the passed in threat model to the approved version

    """

    # Get the ID of the TM from the model

    # Get the approved version from the index metadata

    # Get the approved version and hydrate it (not sure how to do this?)

    # Measure distance between two

def distance_to_template(config:dict, execution_env, doc_model:dict, template:dict):
    """ 
    Measure the distance of the passed in threat model to a template

    """

    output = _output(config)

    assign_row_identifiers(doc_model)
    assign_parent_keys(doc_model)
    assign_row_identifiers(template)
    assign_parent_keys(template)

    return measure_distance.distances(config, output, doc_model, template)