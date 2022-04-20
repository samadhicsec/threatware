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
        
    def getConfluenceConnectionCredentials(self):
        
        confluence_config = configparser.ConfigParser()

        confluence_creds_file = self.config.get("confluence_creds_file", "~/.atlassian")
        if confluence_creds_file.startswith("~"):
            confluence_creds_file = os.path.expanduser(confluence_creds_file)        
        confluence_config.read(confluence_creds_file)

        confluence_creds_section = self.config.get("confluence_creds_section", "DEFAULT")
    
        return dict(confluence_config.items(confluence_creds_section))

        
    def getGoogleCredentials(self):

        credentials = {}
        credentials["credentials-file"] = self.config.get("google", {}).get("credentials_file", "convertors/gdoc_convertor/credentials.json")
        credentials["token-file"] = self.config.get("google", {}).get("token_file", "convertors/gdoc_convertor/token.json")

        # For local testing with service credentials
        #svc_credentials_path = "convertors/gdoc_convertor/svc_credentials.json"
        #svc_credentials_fullpath = Path.joinpath(Path.cwd(), svc_credentials_path)
        #with open(svc_credentials_fullpath, 'r') as creds_file:
        #        credentials = json.load(creds_file)

        return credentials

    def getGitCredentials(self):

        # This should never be called for the CLI provider
        logger.error("Git credentials should not be requested for CLI provider")
        return None
        
        # For local container testing with git credentials
        # credentials = {}
        # with open("/root/.ssh/threatware_ed25519", 'r') as ssh_private_file:
        #     credentials["private-key"] = ssh_private_file.read()
        # with open("/root/.ssh/threatware_ed25519.pub", 'r') as ssh_public_file:
        #     credentials["public-key"] = ssh_public_file.read()

        # return credentials

def load(config:dict):

    return CLIContext(config)