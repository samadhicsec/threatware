#!/usr/bin/env python3

import logging
import data.get as get
import data.output
import data.map

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def parse(value_def, input):

    logger.debug(f'Entering: value_def = {value_def.keys() if value_def else None}')

    if not value_def:
        # There is nothing defined to change the input, so we can just return the input
        return input

    output = None

    #   Process scheme field 
    #       get-data: 
    #           query ...
    #

    # If there is a get-data section use that to extract the data we want to map
    data_value = get.parse(value_def.get("get-data",{}), input)

    #   Process scheme field 
    #       map-data: 
    #           - key ...
    #             value ...
    #

    # If there is a map-data section we'll use that to map data to output
    map_data_def = value_def.get("map-data", [])
    
    # If there is no mapping, then we just return the value (no more recursion into this method)
    if map_data_def is None or len(map_data_def) == 0:
        logger.debug("No map_data so directly passing output of get-data to output-data")
        output = data_value
    else:
        # The data returned by get-data needs to be mapped to correct values.  If get-data returned a list then each item in the list
        # needs to be passed for mapping
        if isinstance(data_value, list):
            logger.debug(f"A list of {len(data_value)} data inputs will be mapped")
            
            # If the data_value is a list, then for each item in the list we will apply the map_data_def.  We track output in a list.
            output_list = []
            for list_item in data_value:

                # Map an item of the data list
                # If map-data:value exists it will call back into this method with the list item as input
                output_dict = data.map.parse(map_data_def, list_item)
                
                logger.debug(f"Mapped data {output_dict}")
                output_list.append(output_dict)
            
            output = output_list
        else:
            
            # Map the data
            output_dict = data.map.parse(map_data_def, data_value)

            logger.debug(f"Mapped data {output_dict}")
            
            output = output_dict

    #   Process scheme field 
    #       output-data: 
    #           type: ...
    #           post-processor: ...
    #

    output_data_def = value_def.get("output-data", {})
    output = data.output.process(output_data_def, output)

    logger.debug(f'Leaving: value_def = {value_def.keys()}')

    return output