#!/usr/bin/env python3
"""
Measure the distance between two threat models
"""


# We can tag fields with 'measure' or 'risk_analysis', and pass in a doc and a template, and compare values in these fields.  The template needn't be an actual template and could be any other TM, like a golden TM

import logging
from pickle import FALSE
import data
import measure.measure_config as manage_config
from measure.measure_output import MeasureOutput
from measure.measure_output import Measurement
from data import find
from utils import keymaster, match

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def _get_tag_from_parts(tag_tuple, exclude_filter = False):

    tag_prefix, tag_model_name, tag_compare_name, tag_filter = tag_tuple

    tag = tag_prefix + "/" + tag_model_name + "/" + tag_compare_name

    if not exclude_filter and tag_filter is not None:
        tag = tag + "/" + tag_filter

    return tag

def _get_measure_tag_parts(reftag:str, exclude_filter = False):

    # Split tag into parts
    tag_parts = reftag.split("/")

    if len(tag_parts) < 3 or len(tag_parts) > 4:
        return None, None, None, None

    tag_prefix = tag_parts[0]
    tag_model_name = tag_parts[1]
    tag_compare_name = tag_parts[2]
    tag_filter = None
    if not exclude_filter and len(tag_parts) == 4:
        tag_filter = tag_parts[3]

    return tag_prefix, tag_model_name, tag_compare_name, tag_filter

def _get_measurement_parameters(config:dict, model:dict):

    measuremeant_prefix = config["measure-tag"]["prefix"]
    measurement_tuple_keyword = config["measure-tag"]["measure-compare-tuple"]


    # Find every key with a tag that starts with the configured prefix.
    all_measure_tagged_keys = find.keys_with_tag_matching_regex(model, "^" + measuremeant_prefix + ".*$")

    targets = []

    for key_entry, value_entry in all_measure_tagged_keys:

        data_tag = keymaster.get_data_tag_for_key(key_entry)

        for tag in key_entry.getTags():

            base_tag_tuple = _get_measure_tag_parts(tag, exclude_filter=True)
            tag_prefix, tag_model_name, tag_compare_name, _ = base_tag_tuple

            if measuremeant_prefix != tag_prefix:
                # We are only looking at tags with the desired prefix
                continue

            # Each data-tag and tuple will be that same across all rows, so no need to find these more than once
            target_exists = False
            for existing_data_tag, _, existing_tag_tuple in targets:
                if existing_data_tag == data_tag and existing_tag_tuple == base_tag_tuple:
                    target_exists = True
                    break
            if target_exists:
                continue

            if measurement_tuple_keyword not in tag_compare_name:
                # Then simple add a target
                target = data_tag, [(key_entry, _get_measure_tag_parts(tag))], base_tag_tuple
                if target not in targets:
                    logger.debug(f"Adding measure target '{target}'")
                    targets.append(target)
            else:
                # Need every key name that includes 'tuple' in the row
                row_key = keymaster.get_row_identifier_for_key(key_entry)
                if row_key is None:
                    logger.warning(f"No field with tag 'row-identifier' was found in data tagged '{data_tag}'. Ignoring.")
                    continue
                row_list = row_key.getProperty("row")
                
                # Need to find matching keys that may also have a filter
                keyvalues = find.keys_with_tag_matching_regex(row_list, "^" + _get_tag_from_parts(base_tag_tuple, exclude_filter=True) + "(/.*)?$")
                key_list = []
                tag_tuple_list = []
                for dict_key, _ in keyvalues:
                    if dict_key.name not in key_list:
                        key_list.append(dict_key)
                        tag_tuple_list.append(_get_full_tag_tuple_from_base(dict_key, base_tag_tuple))

                if len(key_list) < 2:
                    logger.warning(f"A '{measuremeant_prefix}' tag with 'tuple' was used but only {len(key_list)} key entry was found in the row.  Tags with 'tuple' should identify multiple keys.")
              
                # Add the base tag_tuple, excluding any filter
                target = data_tag, list(zip(key_list, tag_tuple_list)), _get_measure_tag_parts(_get_tag_from_parts(base_tag_tuple, exclude_filter=True))
                
                if target not in targets:
                    logger.debug(f"Adding measure target '{target}'")
                    targets.append(target)

    return targets

def _get_full_tag_tuple_from_base(key, base_tag_tuple):

    for tag in key.getTags():
        key_tag_tuple = _get_measure_tag_parts(tag)
        if key_tag_tuple[0] == base_tag_tuple[0] and key_tag_tuple[1] == base_tag_tuple[1] and key_tag_tuple[2] == base_tag_tuple[2]:
            return key_tag_tuple

    logger.warning(f"Could not find base tag '{base_tag_tuple}' on key '{key}'")
    return base_tag_tuple

def _filter_row(config, key_values, base_tag_tuple):
    """ Determines if any filtered doesn't match """

    filters = config["filters"]

    for key, value in key_values:
        key_full_tag_tuple = _get_full_tag_tuple_from_base(key, base_tag_tuple)
        if (tag_filter := key_full_tag_tuple[3]) is not None:
            if tag_filter in filters:
                filter = filters[tag_filter]
                if not match.equals(value, filter):
                    return True
            else:
                logger.warning(f"Could not find filter '{tag_filter}'.  Ignoring")

    return False

def _get_row_of_measured_key_values(config, row_list, base_tag_tuple):

    tag = _get_tag_from_parts(base_tag_tuple)

    #key_values = find.keys_with_tag(row_list, tag)
    # Need to find matching keys that may also have a filter
    row_key_values = find.keys_with_tag_matching_regex(row_list, "^" + _get_tag_from_parts(base_tag_tuple, exclude_filter=True) + "(/.*)?$")

    # TODO If not a tuple, then we only want a single key/value, which should match the key passed in

    if _filter_row(config, row_key_values, base_tag_tuple):
        return None

    return row_key_values

def _get_rows_of_measured_key_values(config, data_tag_value, base_tag_tuple):

    if isinstance(data_tag_value, dict):
        data_tag_value = [data_tag_value]

    rows = []
    for row in data_tag_value:
        row_key_values = _get_row_of_measured_key_values(config, row, base_tag_tuple)
        if row_key_values is not None:
            rows.append(row_key_values)

    return rows

def distance(config:dict, measurement:Measurement, data_tag, base_tag_tuple, this_model:dict, other_model:dict):

    _, this_data_tag_value = find.key_with_tag(this_model, data_tag)
    _, other_data_tag_value = find.key_with_tag(other_model, data_tag)
    
    # Need to get all row values, then extract out the columns to compare, and then compare each column with the other.  There can be multiple columns of the same name

    this_rows = _get_rows_of_measured_key_values(config, this_data_tag_value, base_tag_tuple)
    other_rows = _get_rows_of_measured_key_values(config, other_data_tag_value, base_tag_tuple)

    measurement.addCount(len(other_rows))

    # These loops look through this_model for values that don't exist (are extra), compared to the other_model
    for this_row in this_rows:
        
        match_found = False
        for other_row in other_rows:
            # Go through every other_row, looking for match
            row_match_found = True
        
            # For every measure tag value in this_row
            for this_key, this_value in this_row:
        
                # We want to know if this_value matches a other_value
                col_match_found = False
                for other_key, other_value in other_row:
                    # The same tag could be used in multiple columns, so make sure we are comparing matching columns
                    if this_key.name == other_key.name:
                        # Check if the other_value is a match
                        # TODO account for partial matches
                        if match.equals(this_value, other_value):
                            col_match_found = True
                            break

                if not col_match_found:
                    row_match_found = False
                    break

            if row_match_found:
                match_found = True
                break
        
        if not match_found:
            # Add the 'this' value to the measurement, as it's value was not found in 'other'
            measurement.addDistance(this_row)

    return


def distances(config:dict, output:MeasureOutput, this_model:dict, other_model:dict):

    measure_from_this_model = config["measure-tag"]["measure-this-model-against-other-model"]
    measure_from_other_model = config["measure-tag"]["measure-other-model-against-this-model"]
    measure_compare_missing = config["measure-tag"]["measure-compare-missing"]
    measure_compare_extra = config["measure-tag"]["measure-compare-extra"]

    # Need to get sets of sections, columns and measure labels.  Complicated because multiple different lables can be used in a section.
    parameters = _get_measurement_parameters(config, this_model)

    this_model_name = find.key_with_tag(this_model, "document-title")[1]
    this_model_version = find.key_with_tag(this_model, "current-version")[1]
    other_model_name = find.key_with_tag(other_model, "document-title")[1]
    other_model_version = find.key_with_tag(other_model, "current-version")[1]

    for data_tag, key_tag_list, base_tag_tuple in parameters:

        # Setup the measurement capture
        data_tag_key, data_tag_value = find.key_with_tag(this_model, data_tag)
        section_key = keymaster.get_section_for_key(data_tag_key)
        measurement = Measurement(config, this_model_name, this_model_version, other_model_name, other_model_version, section_key, base_tag_tuple, key_tag_list)

        tag_prefix, tag_measure_direction, tag_compare_name, tag_filter = base_tag_tuple
        # Calculate the distance
        #if match.equals(tag_measure_direction, measure_from_this_model):
        if match.equals(tag_measure_direction, measure_from_other_model) and measure_compare_missing in tag_compare_name or \
            match.equals(tag_measure_direction, measure_from_this_model) and measure_compare_extra in tag_compare_name:
            # measure/from-other/missing is equivalent to measure/from-this/extra
            distance(config, measurement, data_tag, base_tag_tuple, this_model, other_model)
        #elif match.equals(tag_measure_direction, measure_from_other_model):
        elif match.equals(tag_measure_direction, measure_from_this_model) and measure_compare_missing in tag_compare_name or \
            match.equals(tag_measure_direction, measure_from_other_model) and measure_compare_extra in tag_compare_name:
            # measure/from-this/missing is equivalent to measure/from-other/extra
            # Note, we simple switch the order of the models we pass in
            distance(config, measurement, data_tag, base_tag_tuple, other_model, this_model)
        else:
            # TODO capture error in measurement output
            logger.warning(f"Measure tag found referencing unknown model '{tag_measure_direction}'.  Ignoring")
            continue

        output.addMeasure(measurement)

    output.setSuccess("success", {"this_model_name":this_model_name, "other_model_name":other_model_name})
    return output    
    

