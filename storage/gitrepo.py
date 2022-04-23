#!/usr/bin/env python3
"""
Classes to use git as a storage repository for threat model metadata
"""
import logging
import os
from pathlib import Path
from io import StringIO
import sh
from sh.contrib import git
from sh import rm
import utils.shell as shell
import utils.match as match
from utils import load_yaml
from utils.error import StorageError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class GitStorage:

    # Class variable to indicate if we are in a containerised environment
    containerised = False

    def __init__(self, config:dict, execution_env):

        self.gitrepo_config = config.get("gitrepo", {}) 
        self.base_storage_dir = self.gitrepo_config.get("base-storage-dir", "/tmp/")
        self.remote = self.gitrepo_config.get("remote")
        self.default_branch = self.gitrepo_config.get("default-branch", "approved")
        self.is_entered = False

        self.repodirname = "tm_mgmt"
        self.repodir = Path(self.base_storage_dir).joinpath(self.repodirname)

        # Need to setup git depending on the environment we are in

        if GitStorage.containerised:
            # To work in lambda which doesn't have '/dev/fd' (which this argument that defaults to true relies on), we need to set this to False.  Hope this has no negative side effects
            shell.global_kwargs["_close_fds"] = False
            # To work in lambda which only allows us to write to /tmp, we need to configure ssh to use the config file there, and we need to set this env var so git uses ssh with this file
            git_env = os.environ.copy()
            #git_env["GIT_SSH_COMMAND"] = "ssh -F /tmp/.ssh/config"
            git_env["GIT_SSH_COMMAND"] = "ssh -F " + str(self.repodir)
            shell.global_kwargs["_env"] = git_env

            # The dockerfile created a symlink to /tmp/.ssh, but in AWS lambda that doesn't exist, so we need to create it.
            os.makedirs("/tmp/.ssh", exist_ok=True)

            # Write private and public keys to /tmp/.ssh/key and /tmp/.ssh/key.pub
            git_keys = execution_env.getGitCredentials()
            git_private_key = git_keys["private-key"]
            git_public_key = git_keys["public-key"]
            git_public_key_list = git_public_key.split(" ")
            if len(git_public_key_list) != 3:
                raise StorageError(None, None)
            git_alg, git_key, self.git_email = git_public_key_list[0], git_public_key_list[1], git_public_key_list[2]

            # TODO: ssh is REALLY fussy about the private key file contents, so we need to do a sanity check on the contents we read in and ensure it will parse correctly
            # Need \n at the end of each line, ESPECIALLY the last line needs a \n (without the file will not parse)
            # Lines need to be a certain length I believe
            # Header and footer lines need to be be perfect i.e. "-----BEGIN OPENSSH PRIVATE KEY-----\n", "-----END OPENSSH PRIVATE KEY-----\n"

            #old_umask = os.umask(0)
            with open(os.open("/tmp/.ssh/key", os.O_CREAT | os.O_WRONLY, 0o600), "w") as key_file:
                key_file.writelines(git_private_key)
                # Private key must have restricted access or git complains.
            with open("/tmp/.ssh/key.pub", "w") as key_file:
                key_file.writelines(git_public_key)

            # Write .ssh/config for the key file
            with open("/tmp/.ssh/config", "w") as ssh_config:
                ssh_config.writelines(f"IdentityFile=/tmp/.ssh/key")

            # Get the host from the 'remote' value of the form 'protocol@host:path'
            if not self.remote.startswith("git@"):
                raise StorageError(None, None)
            git_host = (self.remote.split("@")[1]).split(":")[0]

            # Need to populate .ssh/known_hosts with remote pub key i.e. ssh-keyscan -t ed25519 github.com >> /tmp/.ssh/known_hosts
            shell.run(self.base_storage_dir, sh.ssh_keyscan, ["-t", git_alg, git_host], _out="/tmp/.ssh/known_hosts")

    def _not_entered(self):
        if not self.is_entered:
            logger.error(f"Cannot perform action outside of 'with' statement")
            raise StorageError("internal-error", {})

        return False

    # def _run(self, directory, command, *args, **kwargs):

    #     if "_out" not in kwargs:
    #         kwargs["_out"] = logger.debug

    #     with pushd(directory):  
    #         try:
    #             logger.debug(f"Running '{command.__name__}' with args '{args}'")
    #             command(*args, **kwargs)
    #         except ErrorReturnCode as erc:
    #             logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
    #             return False

    #     return True        

    def __enter__(self):

        buf = StringIO()
        
        if Path(self.repodir).is_dir():
            logger.warning(f"Directory '{self.repodir}' already exists")

        if not shell.run(self.base_storage_dir, sh.ls, ["-alR"], _out=buf, _err_to_out=True):
            raise StorageError("internal-error", {})

        if not shell.run(self.base_storage_dir, git.clone, ["--no-checkout", self.remote, self.repodirname], _out=buf, _err_to_out=True):
            outdata = buf.getvalue()
            logger.debug(f"{outdata}")
            logger.error(f"Could not clone repo '{self.remote}'")
            raise StorageError("internal-error", {})

        # if not shell.run(self.base_storage_dir, git.clone, ["--no-checkout", self.remote], _out=buf, _err_to_out=True):
        #     logger.error(f"Could not clone repo '{self.remote}'")
        #     raise StorageError("internal-error", {})

        

        # # Get the directory where the code was cloned into
        # for line in outdata.splitlines():
        #     if line.startswith("Cloning into '") and line .endswith("'..."):
        #         self.repodirname = line.split("'")[1]
        #         break

        # self.repodir = Path(self.base_storage_dir).joinpath(self.repodirname)

        if GitStorage.containerised:
            # Git must know who the user is before it can commit. Configure git user.name and user.email
            shell.run(self.repodir, git.config, ["user.name", self.gitrepo_config.get("git-user-name", self.git_email)])
            shell.run(self.repodir, git.config, ["user.email", self.gitrepo_config.get("git-user-email", self.git_email)])

        #if not shell.run(self.repodir, git, ["sparse-checkout", "init", "--cone"]):
        if not shell.run(self.repodir, git, ["sparse-checkout", "init"]):
            logger.error(f"Could not sparse-checkout init")
            raise StorageError("internal-error", {})

        # Above command will set sparse-checkout pattern, but to retrieve root dir contents, we need to do a checkout (git > 2.25)
        if not shell.run(self.repodir, git, ["checkout"]):
            # This could have failed because there is no remote branch to checkout i.e. repo is brand new
            if not self.remote_branch_exists(self.default_branch):
                # Create local branch
                if not shell.run(self.repodir, git.checkout, ["-b", self.default_branch]):
                    logger.error(f"Unable to create local branch '{self.default_branch}'")
                    raise StorageError("internal-error", {})    
                # Do an initial local commit
                if not shell.run(self.repodir, git.commit, ["--allow-empty", "-m", "Creating default branch"]):
                    logger.error(f"Unable to commit empty branch '{self.default_branch}'")
                    raise StorageError("internal-error", {})
                # Create default remote branch
                if not shell.run(self.repodir, git.push, ["-u", "origin", self.default_branch + ":" + self.default_branch]):
                    logger.error(f"Unable to push initial commit for branch '{self.default_branch}'")
                    raise StorageError("internal-error", {})
            else:
                logger.error(f"Could not checkout root directory contents")
                raise StorageError("internal-error", {})
        

        self.is_entered = True

    def remote_branch_exists(self, branch:str):

        remote_branch_exists_var = False

        def _check_for_remote_branch(output):
            nonlocal remote_branch_exists_var
            if not remote_branch_exists_var:
                for line in str(output).splitlines():
                    if line.endswith("refs/heads/" + self.branch):
                        remote_branch_exists_var = True
                        return

        if not shell.run(os.getcwd(), git, ["ls-remote", "--heads", self.remote], _out=_check_for_remote_branch):
            logger.error(f"Could not get list of remote heads for '{self.remote}'")
            raise StorageError("internal-error", {})
        
        return remote_branch_exists_var

    def _is_default_branch(self, branch:str):
        if match.is_empty(branch) or match.equals(self.default_branch, branch):
            logger.error(f"Cannot commit directly to default branch")
            raise StorageError("internal-error", {})

        return False

    def branch_update(self, branch:str):
        """ Switches to either a local branch using existing remote branch (fetching any existing changes on that branch), or creates a new local branch """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            if not shell.run(self.repodir, git.checkout, ["-b", self.branch, "origin/" + self.branch]):
                logger.error(f"Could not checkout remote branch '{self.branch}'")
                raise StorageError("internal-error", {})
        else:
            if not shell.run(self.repodir, git.checkout, ["-b", self.branch]):
                logger.error(f"Could not checkout local branch '{self.branch}'")
                raise StorageError("internal-error", {})
    
    def branch_replace(self, branch:str):
        """ Switches to a local branch, deleting any existing remote branch (ignoring any existing changes on that branch) """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            if not shell.run(self.repodir, git.push, ["origin", "-d", self.branch]):
                logger.error(f"Failed to delete remote branch '{self.branch}'")
                raise StorageError("internal-error", {})

        if not shell.run(self.repodir, git.checkout, ["-b", self.branch]):
            logger.error(f"Failed to checkout local branch '{self.branch}'")
            raise StorageError("internal-error", {})

    def is_merged_to_default(self, branch:str):

        if self._not_entered():
            return

        buf = StringIO()

        # i.e. git branch -r --merged approved
        if not shell.run(self.repodir, git.branch, ["-r", "--merged", self.default_branch], _out=buf, _err_to_out=True):
            logger.error(f"Could not determine if '{self.branch}' has been merged or not")
            raise StorageError("internal-error", {})

        outdata = buf.getvalue()
        logger.debug(f"{outdata}")

        for line in outdata.splitlines():
            if line.endswith(branch):
                return True

        return False


    def commit(self, message:str = ""):

        if self._not_entered():
            return

        if self._is_default_branch(self.branch):
            return

        if not shell.run(self.repodir, git.add, ["."]):
            logger.error(f"Failed to git add local changes")
            raise StorageError("internal-error", {})
        if not shell.run(self.repodir, git.commit, ["-m", message]):
            logger.error(f"Failed to git commit local changes")
            raise StorageError("internal-error", {})
        if not shell.run(self.repodir, git.push, ["-u", "origin", self.branch]):
            logger.error(f"Failed to git push local changes to remote")
            raise StorageError("internal-error", {})
    
    def __exit__(self, exc_type, exc_value, traceback):

        # Delete the repo we checked out.  
        shell.run(self.base_storage_dir, rm, ["-rf", self.repodir])

        self.is_entered = False

    def load_yaml(self, class_list:list, relative_file_path:str) -> dict:

        file_path = Path(self.repodir).joinpath(relative_file_path)
        if file_path.is_file():
            return load_yaml.yaml_file_to_dict(file_path, class_list)

        return None

    def write_yaml(self, class_list:list, relative_file_path:str, contents):

        file_path = Path(self.repodir).joinpath(relative_file_path)
        if not file_path.is_file():
            # Try to make the directory, as that at least needs to exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

        load_yaml.class_to_yaml_file(class_list, contents, file_path)

