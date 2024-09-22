#!/usr/bin/env python3
"""
Makes available configuration for AWS Lambda execution context
"""

import logging
import os
import json
from sh import ssh_keyscan
from sh.contrib import git
from pathlib import Path
import utils.shell as shell
from utils.error import StorageError
import boto3
from botocore.exceptions import ClientError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class AWSLambdaContext:

    def __init__(self, config:dict):
        # Needs to be able to handle an empty config because providers may get called before config files are available.

        self.config = config
        if "secret_name" in config:
            self.secret_name = config.get("secret_name")
        else:
            # Read from env var if possible
            self.secret_name = os.getenv("THREATWARE_AWS_SECRET_NAME")

        if "region" in config: 
            self.region = config.get("region")
        else:
            # Read from env var if possible
            self.region = os.getenv("THREATWARE_AWS_SECRET_REGION")

        self.secret_dict = {}
        if self.secret_name is not None and self.region is not None:
            self.secret_dict = json.loads(self._get_secret())

    def _get_secret(self):

        # This code taken from https://boto3.amazonaws.com/v1/documentation/api/latest/guide/secrets-manager.html

        secret_name = self.secret_name
        region_name = self.region

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"The requested secret '{secret_name}' was not found")
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                logger.error(f"The request was invalid due to: {e}")
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                logger.error(f"The request had invalid params: {e}")
            elif e.response['Error']['Code'] == 'DecryptionFailure':
                logger.error(f"The requested secret can't be decrypted using the provided KMS key: {e}")
            elif e.response['Error']['Code'] == 'InternalServiceError':
                logger.error(f"An error occurred on service side: {e}")
        else:
            # Secrets Manager decrypts the secret value using the associated KMS CMK
            # Depending on whether the secret was a string or binary, only one of these fields will be populated
            if 'SecretString' in get_secret_value_response:
                text_secret_data = get_secret_value_response['SecretString']
            else:
                logger.error(f"No 'SecretString' was available in secret '{secret_name}'")
                #binary_secret_data = get_secret_value_response['SecretBinary']

        return text_secret_data

    def getConfluenceConnectionCredentials(self):
        
        confluence_conn = json.loads(self.secret_dict.get("confluence"))

        return confluence_conn

    def getGoogleCredentials(self):

        credentials = json.loads(self.secret_dict.get("google"))

        return credentials

    def getGitCredentials(self):

        credentials = json.loads(self.secret_dict.get("git"))

        return credentials
    
    def _format_openssh_private_key(self, key:str) -> str:
        """
        Reformat OpenSSH private key in-case user has just cut and paste

        Ensures OpenSSH header and footer text ends in newline - without this ssh considers the private key file invalid
        """
        openssh_header = "-----BEGIN OPENSSH PRIVATE KEY-----"
        openssh_footer = "-----END OPENSSH PRIVATE KEY-----"

        # Check if key contains correct newline terminated header
        if key.find(openssh_header + "\n") == -1:
            # Check if key contains header, just not newline terminated
            if key.find(openssh_header) != -1:
                # Replace non newline terminated header with newline terminated header
                key = key.replace(openssh_header, openssh_header + "\n")
            else:
                # Not an OpenSSH private key
                return key

        # Check if key contains correct newline terminated footer
        if key.find(openssh_footer + "\n") == -1:
            # Check if key contains footer, just not newline terminated
            if key.find(openssh_footer) != -1:
                # Replace non newline terminated footer with newline terminated footer
                key = key.replace(openssh_footer, openssh_footer + "\n")
            else:
                logger.error("Private does not have an OpenSSH footer")
                # Not an OpenSSH private key
                return key

        return key

    def setupGit(self, remote:str, base_storage_dir:str):

        # On AWS Lambda, to setup git, since we can't write to the local user's /home directory, we must
        # configure git in the only location we can write to, which is /tmp

        if remote.startswith("git@"):
            logger.info("Setting up git to use SSH credentials in /tmp")
            ssh_path = Path.joinpath(Path(base_storage_dir), ".ssh")
            ssh_config_path = str(Path.joinpath(ssh_path, "config"))
            ssh_private_key_path = str(Path.joinpath(ssh_path, "key"))
            ssh_public_key_path = str(Path.joinpath(ssh_path, "key.pub"))
            ssh_known_hosts_path = str(Path.joinpath(ssh_path, "known_hosts"))
            ssh_path = str(ssh_path)

            # To work in lambda which doesn't have '/dev/fd' (which this argument that defaults to true relies on), we need to set this to False.  Hope this has no negative side effects
            shell.global_kwargs["_close_fds"] = False
            # To work in lambda, which seems to have no or few TTYs (because you get errors about it running out of them), set this to False
            shell.global_kwargs["_tty_out"] = False
            # To work in lambda which only allows us to write to /tmp, we need to configure ssh to use the config file there, and we need to set this env var so git uses ssh with this file
            git_env = os.environ.copy()
            git_env["GIT_SSH_COMMAND"] = "ssh -F " + ssh_config_path
            shell.global_kwargs["_env"] = git_env

            # The dockerfile created a symlink to /tmp/.ssh, but in AWS lambda that doesn't exist, so we need to create it.
            os.makedirs(ssh_path, exist_ok=True)

            # Write private and public keys to /tmp/.ssh/key and /tmp/.ssh/key.pub
            git_keys = self.getGitCredentials()
            if git_keys is None or len(git_keys) == 0:
                raise StorageError("storage.no-git-credentials", {})
            git_private_key = git_keys["private-key"]
            git_public_key = git_keys["public-key"]
            git_public_key_list = git_public_key.split(" ")
            if len(git_public_key_list) != 3:
                logger.error(f"Expected public key to consist of 3 space separated parts, instead found {len(git_public_key_list)} parts")
                raise StorageError("internal-error", None)
            git_alg, git_key, git_email = git_public_key_list[0], git_public_key_list[1], git_public_key_list[2]

            # ssh is REALLY fussy about the private key file contents, so we need to do a sanity check on the contents we read in and ensure it will parse correctly
            # Header and footer lines need to be be perfect i.e. "-----BEGIN OPENSSH PRIVATE KEY-----\n", "-----END OPENSSH PRIVATE KEY-----\n"
            git_private_key = self._format_openssh_private_key(git_private_key)

            with open(os.open(ssh_private_key_path, os.O_CREAT | os.O_WRONLY, 0o600), "w") as key_file:
                key_file.writelines(git_private_key)
                # Private key must have restricted access or git complains.
            with open(ssh_public_key_path, "w") as key_file:
                key_file.writelines(git_public_key)

            # Write .ssh/config for the key file
            with open(ssh_config_path, "w") as ssh_config:
                ssh_config.writelines(["IdentityFile=" + ssh_private_key_path + "\n", "UserKnownHostsFile=" + ssh_known_hosts_path + "\n"])

            # Get the host from the 'remote' value of the form 'protocol@host:path'
            #if not self.remote.startswith("git@"):
            #    logger.error("Currently only remotes using 'git@' are supported")
            #    raise StorageError("internal-error", None)
            git_host = (remote.split("@")[1]).split(":")[0]

            # Need to populate .ssh/known_hosts with remote pub key i.e. ssh-keyscan -t ed25519 github.com >> /tmp/.ssh/known_hosts
            shell.run(base_storage_dir, ssh_keyscan, ["-t", git_alg, git_host], _out=ssh_known_hosts_path)

            # Change the location where git config looks for the config file
            os.environ["XDG_CONFIG_HOME"] = base_storage_dir
            os.makedirs(os.path.join(base_storage_dir, "git"), exist_ok=True)
            # Other options are to set
            # GIT_CONFIG_GLOBAL to the name of the global config file to use
            # GIT_CONFIG_SYSTEM to /dev/null to prevent git from reading the system config file (or set GIT_CONFIG_NOSYSTEM to 1)

            # Git must know who the user is before it can commit. Configure git user.name and user.email
            shell.run(base_storage_dir, git.config, ["--global", "user.name", "threatware"])
            shell.run(base_storage_dir, git.config, ["--global", "user.email", "threatware"])

        elif remote.startswith("http"):
            logger.info("Using git with anonymous HTTP")
        else:
            logger.warning("Unrecognised git remote, assuming anonymous HTTP")

    def get_config_base_dir(self, suggested_base_dir):
        """ Return the directory where we expect the configuration file to be based 
        
        Returns
        -------
        str : The suggested base directory to find configuration file
        bool : Whether this environment is ephemeral (config will not persist between invocations)
        """

        # We can only write to /tmp for lambdas, so need to check suggestion does that, and if not move it there
        real_suggested_base_dir = os.path.realpath(os.path.normpath(suggested_base_dir))

        # Compare dir /tmp to the shared path between /tmp and the suggestion (which will be /tmp if the suggested path starts with /tmp)
        if os.path.samefile("/tmp", os.path.commonpath(["/tmp", real_suggested_base_dir])):
            base_dir = real_suggested_base_dir
        else:
            if os.path.isabs(real_suggested_base_dir):
                head, tail = os.path.split(real_suggested_base_dir)
                base_dir = os.path.join("/tmp", tail)
            else:
                base_dir = os.path.join("/tmp", real_suggested_base_dir)

        # The config will NOT persist after execution
        return base_dir, True

def load(config:dict):

    return AWSLambdaContext(config)