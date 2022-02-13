#!/usr/bin/env python3
"""
Makes available configuration for CLI execution context
"""

import os
import configparser
import logging

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class CLIContext:

    def __init__(self, config:dict):

        self.config = config
        self.confluence_creds_file = config.get("confluence_creds_file", "~/.atlassian")
        if self.confluence_creds_file.startswith("~"):
            self.confluence_creds_file = os.path.expanduser(self.confluence_creds_file)
        self.confluence_creds_section = config.get("confluence_creds_section", "DEFAULT")

    def getConfluenceConnectionCredentials(self):
        
        config = configparser.ConfigParser()
        config.read(self.confluence_creds_file)
    
        if not config.has_option(self.confluence_creds_section, 'url'):
            logger.error(f"No 'url' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
        if not config.has_option(self.confluence_creds_section, 'username'):
            logger.error(f"No 'username' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
        if not config.has_option(self.confluence_creds_section, 'api_token'):
            logger.error(f"No 'api_token' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
    
        return {"url":config.get(self.confluence_creds_section, 'url'), "username":config.get(self.confluence_creds_section, 'username'), "api_token":config.get(self.confluence_creds_section, 'api_token')}



def load(config:dict):

    return CLIContext(config)