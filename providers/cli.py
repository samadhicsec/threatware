#!/usr/bin/env python3
"""
Makes available configuration for CLI execution context
"""

import os
import configparser
import logging
from utils.error import ProviderError
from utils.config import ConfigBase

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class CLIContext:

    def __init__(self, config:dict):

        self.config = config
        
    def getConfluenceConnectionCredentials(self):
        
        confluence_config = configparser.ConfigParser()

        confluence_creds_file = ConfigBase.getConfigPath(self.config.get("confluence", {}).get("creds_config_file", ".atlassian"))
        confluence_creds_file = os.path.expanduser(confluence_creds_file)        
        confluence_config.read(confluence_creds_file)

        confluence_creds_section = self.config.get("confluence", {}).get("creds_config_section", "DEFAULT")

        confluence_config_dict = dict(confluence_config.items(confluence_creds_section))

        if len(confluence_config_dict) == 0:
            logger.error(f"The contents of the Confluence configuration file '{confluence_creds_file}' was empty")
            raise ProviderError("providers.emtpyConfluenceConfig", {"providers":{"creds_file":confluence_creds_file}})
    
        return confluence_config_dict

        
    def getGoogleCredentials(self):

        credentials = {}
        credentials["credentials-file"] = ConfigBase.getConfigPath(self.config.get("google", {}).get("credentials_file", "credentials.json"))
        credentials["token-file"] = ConfigBase.getConfigPath(self.config.get("google", {}).get("token_file", "token.json"))

        if not os.path.exists(credentials["credentials-file"]):
            logger.error(f"The Google credentials file '{credentials['credentials-file']}' does not exist")
            raise ProviderError("providers.noGoolgeCredsFile", {"providers":{"creds_file":credentials["credentials-file"]}})

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

    def get_config_base_dir(self, suggested_base_dir):
        """ Return the directory where we expect the configuration file to be based 
        
        Returns
        -------
        str : The suggested base directory to find configuration file
        bool : Whether this environment is ephemeral (config will not persist between invocations)
        """

        # Just return the suggestion whe using the CLI.  The config will persist after execution
        return suggested_base_dir, False


def load(config:dict):

    return CLIContext(config)