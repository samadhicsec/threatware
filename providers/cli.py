#!/usr/bin/env python3
"""
Makes available configuration for CLI execution context
"""

import os
import configparser
import logging
import json
from pathlib import Path

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
    
        return dict(config.items(self.confluence_creds_section))

        # if not config.has_option(self.confluence_creds_section, 'url'):
        #     logger.error(f"No 'url' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
        # if not config.has_option(self.confluence_creds_section, 'username'):
        #     logger.error(f"No 'username' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
        # if not config.has_option(self.confluence_creds_section, 'api_token'):
        #     logger.error(f"No 'api_token' field found in the '{self.confluence_creds_file}' config file in section '{self.confluence_creds_section}'")
    
        # return {"url":config.get(self.confluence_creds_section, 'url'), "username":config.get(self.confluence_creds_section, 'username'), "api_token":config.get(self.confluence_creds_section, 'api_token')}

    def getGoogleCredentials(self):

        credentials = {}
        credentials["credentials-file"] = self.config.get("google", {}).get("credentials_file", "convertors/gdoc_convertor/credentials.json")
        credentials["token-file"] = self.config.get("google", {}).get("token_file", "convertors/gdoc_convertor/token.json")

        # Fopr local testing with service credentials
        #svc_credentials_path = "convertors/gdoc_convertor/svc_credentials.json"
        #svc_credentials_fullpath = Path.joinpath(Path.cwd(), svc_credentials_path)
        #with open(svc_credentials_fullpath, 'r') as creds_file:
        #        credentials = json.load(creds_file)

        return credentials

def load(config:dict):

    return CLIContext(config)