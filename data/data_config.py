#!/usr/bin/env python3
"""
Configuration class to store config for data module
"""

import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


class DataConfig:
    """ Stores configuration information for converting document parts to models """

    config:dict
    _output_remove_na:bool
    _output_remove_na_tags:list

    @classmethod
    def init(cls, config:dict = {}):

        cls.config = config

        cls._output_remove_na = config.get("output", {}).get("list-with-single-not-applicable-entry", {}).get("remove", True)
        cls._output_remove_na_tags = config.get("output", {}).get("list-with-single-not-applicable-entry", {}).get("apply-tags", [])

    @classmethod
    def remove_na_single_list_entry(cls):
        """ Config for removing list entries with a single 'Not Application' value """
        return cls._output_remove_na, cls._output_remove_na_tags

