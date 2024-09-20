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
        if match.is_empty(self.remote):
            logger.error("Remote repo is empty")
            raise StorageError("storage.no-git-repo", None)
        self.default_branch = self.gitrepo_config.get("default-branch", "approved")
        self.is_entered = False

        self.repodirname = "tm_mgmt"
        self.repodir = str(Path(self.base_storage_dir).joinpath(self.repodirname))

        # Need to setup git depending on the environment we are in
        execution_env.setupGit(self.remote, self.base_storage_dir)


    def _not_entered(self):
        if not self.is_entered:
            logger.error(f"Cannot perform action outside of 'with' statement")
            raise StorageError("internal-error", {})

        return False


    def __enter__(self):

        buf = StringIO()
        
        if Path(self.repodir).is_dir():
            logger.warning(f"Directory '{self.repodir}' already exists")

        if not shell.run(self.base_storage_dir, git.clone, ["--no-checkout", self.remote, self.repodirname], _out=buf, _err_to_out=True):
            outdata = buf.getvalue()
            logger.debug(f"{outdata}")
            logger.error(f"Could not clone repo '{self.remote}'")
            raise StorageError("internal-error", {})

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

        return self


    def checkout_directory(self, dir_name:str):

        # Fetch the directory containing the metadata for the TM ID.  If it doesn't exist, nothing is downloaded
        if not shell.run(self.repodir, git, ["sparse-checkout", "add", dir_name]):
            logger.error(f"Could not sparse-checkout directory '{dir_name}'")
            raise StorageError("internal-error", {})


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

    def write_yaml(self, relative_file_path:str, contents):

        file_path = Path(self.repodir).joinpath(relative_file_path)
        if not file_path.is_file():
            # Try to make the directory, as that at least needs to exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

        load_yaml.class_to_yaml_file(contents, file_path)

