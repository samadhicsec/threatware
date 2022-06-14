#!/usr/bin/env python3
"""
Sets the base directory from which all configuration files are loaded
"""

import logging
import os
from pathlib import Path
from storage.git_permanent_repo import GitPermanentStorage
from utils.error import StorageError
from utils import shell
from sh import rm

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

DEFAULT_CONFIG_BASE_DIR = "~/.threatware"
DEFAULT_CONFIG_REPO = "https://github.com/samadhicsec/threatware-config.git"
DEFAULT_CONFIG_REPO_BRANCH = "v1.0"

class ConfigBase:

    install_dir:str
    base_dir:str
    ephemeral_env:bool

    @classmethod
    def init(cls, execution_env):

        cls._set_install_directory()

        dynamic_config = os.environ.get("THREATWARE_CONFIG_DYNAMIC")
        if dynamic_config == "False":
            # Only if this is explicitly set to "False" do we not try to use dynamic configuration
            cls.base_dir = cls.install_dir
            logger.info("Dynamnic configuration disabled.  Using configuration depoyed with code.")
            return

        suggested_base_dir = os.getenv("THREATWARE_CONFIG_DIR")
        if suggested_base_dir is not None:
            suggested_base_dir = os.path.expandvars(os.path.expanduser(suggested_base_dir))
        else:
            suggested_base_dir = os.path.expanduser(DEFAULT_CONFIG_BASE_DIR)

        # Ask the execution environment where the config should be
        exe_env_root_dir, cls.ephemeral_env = execution_env.get_config_base_dir(suggested_base_dir)

        # Check if the directory exists
        if os.path.isdir(exe_env_root_dir):

            # It exists, so we expect all the config to be present
            cls.base_dir = exe_env_root_dir
            logger.info(f"Using configuration in '{exe_env_root_dir}'")
            return

        else:

            # There is no available configuration.  There are 2 options:
            # - download it, but if that fails
            # - use built-in config, shipped with code
            try: 
                cls._download_config(exe_env_root_dir, execution_env, cls.ephemeral_env)
            finally:
                # Check if the directory exists
                if os.path.isdir(exe_env_root_dir):

                    # It exists, so we expect all the config to be present
                    cls.base_dir = exe_env_root_dir
                    logger.info(f"Using configuration in '{exe_env_root_dir}'")

                else:
                    # Still no config directory, use built-in config
                    cls.base_dir = cls.install_dir
                    logger.info("Failed to acquire dynamic configuration.  Using configuration depoyed with code.")

    @classmethod
    def _set_install_directory(cls):
        """
        Sets the install directory.  The install directory is the root directory of the threatware modules.
        """

        # We are going to cheat and use the fact that we know this file has path utils/config.py
        cls.install_dir = str(Path(__file__).absolute().parent.parent)

    @classmethod
    def _download_config(cls, exe_env_root_dir, execution_env, ephemeral_env):
        """ Try to download configuration from a configured location """

        delete_git_dir = False

        config_git_branch = os.getenv("THREATWARE_CONFIG_REPO_BRANCH")

        config_git_repo = os.getenv("THREATWARE_CONFIG_REPO")
        if config_git_repo is None:
            if not ephemeral_env:
                # Use the threatware default
                config_git_repo = DEFAULT_CONFIG_REPO
                config_git_branch = DEFAULT_CONFIG_REPO_BRANCH
                # No one ever needs to push to this repo, so remove the .git directory
                delete_git_dir = True
            else:
                # No point in downloading the default config as no creds will be set, so no actions will work
                # Just return, so the config shipped with code is used
                return

        # Get the parent and name of the directory to store the config in
        exe_env_root_path = Path(exe_env_root_dir)
        exe_env_root_path_parent = str(exe_env_root_path.parent)
        if not os.path.isdir(exe_env_root_path_parent):
            os.makedirs(exe_env_root_path_parent)
        exe_env_root_path_dir = exe_env_root_path.stem

        git_config = {"gitrepo":{"remote":config_git_repo, "default-branch":config_git_branch, "base-storage-dir":exe_env_root_path_parent}}
        logger.info(f"Cloning dynamic configuration from '{config_git_repo}' (on branch '{config_git_branch}')")
        try:

            perm_storage = GitPermanentStorage(git_config, execution_env)

            perm_storage.clone(exe_env_root_path_dir, config_git_branch)

            if delete_git_dir and exe_env_root_path.joinpath(".git").is_dir():
                shell.run(exe_env_root_dir, rm, ["-rf", ".git"])

        except(StorageError):
            logger.error(f"Failed to download configuration from '{config_git_repo}' to '{exe_env_root_dir}'")
            # We tried and failed
            raise

        return

    @classmethod
    def getConfigPath(cls, config_path:str) -> str:
        """ Returns the config Path from the config base directory.  ConfigBase.init must have been called first. 

        If passed a path already relative to base_dir, just return it
        If passed an absolute path, 
          If relative to the install dir, append the relative path to the CWD to the base_dir.
          If relative to user home, and not an ephemeral env, just return it.
        If passed a relative path, it appends it directly to the base_dir
        """
        config_path_obj = Path(config_path).expanduser()
        if config_path_obj.absolute().is_relative_to(cls.base_dir):
            return str(config_path_obj.absolute())

        if config_path_obj.is_absolute():
            if config_path_obj.absolute().is_relative_to(cls.install_dir):

                return str(Path(cls.base_dir).joinpath(config_path_obj.relative_to(cls.install_dir)))

            elif not cls.ephemeral_env and config_path_obj.absolute().is_relative_to(Path.home()):

                # For persistent environments, configuration files should be able to exist in user's home directory
                return str(config_path_obj.absolute())
                
            else:
                return str(Path(cls.base_dir).joinpath(config_path_obj))
        else:
            return str(Path(cls.base_dir).joinpath(config_path_obj))