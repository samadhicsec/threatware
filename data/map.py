#!/usr/bin/env python3

import logging
import data.value
import data.output
from . import key

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def parse(map_data_def, input) -> dict:
    """ Traverses a map-data: definition and calls value.parse on each value """

    logger.debug(f'Entering: Key count = {len(map_data_def)}, data count = {len(input) if isinstance(input, list) else 1}')

    output = {}

    for key_value in map_data_def:
        if isinstance(key_value["key"], str):
            key_def = key.key(key_value["key"])
        elif isinstance(key_value["key"], dict):
            if (key_def := key.key(key_value["key"]["name"])) is None:
                # TODO throw exception or handle
                logger.error(f"The key {key_value['key']} must have a 'name' key with a non-empty value")
            if (section := key_value["key"].get("section")) is not None:
                # Record a friendly section name for this key, if one exists e.g. a table name
                key_def.addProperty("section", section)
            if (tags := key_value["key"].get("tags")) is not None and isinstance(tags, list):
                key_def.addTags(tags)


        logger.debug(f"Mapping data to '{key_def}'")

        value_def = key_value["value"]
        value = data.value.parse(value_def, input)
        
        logger.debug(f"Mapping '{key_def}':'{value}'")
        output[key_def] = value

        if key_def.getProperty("section") is not None:
            # Let the key reference the value for these high level sections. Makes searching sections e.g. tables, easier given only a tagged key.
            key_def.addProperty("value", value)

    logger.debug(f'Leaving: Key count = {len(map_data_def)}, data count = {len(input) if isinstance(input, list) else 1}')

    return output