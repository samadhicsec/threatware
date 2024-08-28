#!/usr/bin/env python3
"""
Makes available configuration for API execution context
"""

import os
import configparser
from sh import ssh_keyscan
from sh.contrib import git
import utils.shell as shell
import logging
from utils.error import ProviderError
from utils.config import ConfigBase
from providers.cli import CLIContext

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

# API execution environment is the same as CLI, except it's an ephemeral environment
class APIContext:

    def __init__(self, config:dict):

        self.config = config
        self.clicontext = CLIContext(config)
        
    def getConfluenceConnectionCredentials(self):
        
        return self.clicontext.getConfluenceConnectionCredentials()

    def getGoogleCredentials(self):

        return self.clicontext.getGoogleCredentials()

    def getGitCredentials(self):

        # This should never be called for the API provider
        logger.error("Git credentials should not be requested for API provider")
        return None

    def setupGit(self, remote:str, base_storage_dir:str):

        # For the API we rely on the environment to have been already configured for git usage
        if remote.startswith("git@"):
            logger.info("Using local git setup, and local SSH credentials for accessing git repositories")
        elif remote.startswith("http:"):
            logger.info("Using git with anonymous HTTP")
        else:
            logger.warning("Unrecognised git remote, assuming anonymous HTTP")

        # Git must know who the user is before it can commit. Configure git user.name and user.email
        shell.run(os.path.expanduser("~/"), git.config, ["--global", "user.name", "threatware"])
        shell.run(os.path.expanduser("~/"), git.config, ["--global", "user.email", "threatware"])

    def get_config_base_dir(self, suggested_base_dir):
        """ Return the directory where we expect the configuration file to be based 
        
        Returns
        -------
        str : The suggested base directory to find configuration file
        bool : Whether this environment is ephemeral (config will not persist between invocations)
        """

        # Just return the suggestion when using the API.  The config will NOT persist after execution ('True' means ephemeral environment)
        return suggested_base_dir, True


def load(config:dict):

    return APIContext(config)