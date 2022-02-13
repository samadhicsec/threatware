#!/usr/bin/env python3
"""
Classes to use git as a storage repository for threat model metadata
"""
import logging
import os
from pathlib import Path
from io import StringIO
from sh.contrib import git
from sh import pushd
from sh import rm
from sh import ErrorReturnCode
import utils.match as match
from utils import load_yaml
from utils.error import ManageError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class GitStorage:

    def __init__(self, config:dict):

        gitrepo_config = config.get("gitrepo", {}) 
        self.base_storage_dir = gitrepo_config.get("base-storage-dir", "/tmp/")
        self.remote = gitrepo_config.get("remote")
        self.default_branch = gitrepo_config.get("default-branch", "approved")
        self.is_entered = False

    def _not_entered(self):
        if not self.is_entered:
            logger.error(f"Cannot perform action outside of 'with' statement")
            raise ManageError("internal-error", {})

        return False

    def _run(self, directory, command, *args, **kwargs):

        if "_out" not in kwargs:
            kwargs["_out"] = logger.debug

        with pushd(directory):  
            try:
                logger.debug(f"Running '{command.__name__}' with args '{args}'")
                command(*args, **kwargs)
            except ErrorReturnCode as erc:
                logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
                return False

        return True        

    def __enter__(self):

        buf = StringIO()

        if not self._run(self.base_storage_dir, git.clone, ["--no-checkout", self.remote], _out=buf, _err_to_out=True):
            logger.error(f"Could not clone repo '{self.remote}'")
            raise ManageError("internal-error", {})

        outdata = buf.getvalue()
        logger.debug(f"{outdata}")

        # Get the directory where the code was cloned into
        for line in outdata.splitlines():
            if line.startswith("Cloning into '") and line .endswith("'..."):
                self.repodirname = line.split("'")[1]
                break

        self.repodir = Path(self.base_storage_dir).joinpath(self.repodirname)

        if not self._run(self.repodir, git, ["sparse-checkout", "init", "--cone"]):
            logger.error(f"Could not sparse-checkout init")
            raise ManageError("internal-error", {})

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

        if not self._run(os.getcwd(), git, ["ls-remote", "--heads", self.remote], _out=_check_for_remote_branch):
            logger.error(f"Could not get list of remote heads for '{self.remote}'")
            raise ManageError("internal-error", {})
        
        return remote_branch_exists_var

    def _is_default_branch(self, branch:str):
        if match.is_empty(branch) or match.equals(self.default_branch, branch):
            logger.error(f"Cannot commit directly to default branch")
            raise ManageError("internal-error", {})

        return False

    def branch_update(self, branch:str):
        """ Switches to either a local branch using existing remote branch (fetching any existing changes on that branch), or creates a new local branch """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            if not self._run(self.repodir, git.checkout, ["-b", self.branch, "origin/" + self.branch]):
                logger.error(f"Could not checkout remote branch '{self.branch}'")
                raise ManageError("internal-error", {})
        else:
            if not self._run(self.repodir, git.checkout, ["-b", self.branch]):
                logger.error(f"Could not checkout local branch '{self.branch}'")
                raise ManageError("internal-error", {})
    
    def branch_replace(self, branch:str):
        """ Switches to a local branch, deleting any existing remote branch (ignroing any existing changes on that branch) """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            if not self._run(self.repodir, git.push, ["origin", "-d", self.branch]):
                logger.error(f"Failed to delete remote branch '{self.branch}'")
                raise ManageError("internal-error", {})

        if not self._run(self.repodir, git.checkout, ["-b", self.branch]):
            logger.error(f"Failed to checkout local branch '{self.branch}'")
            raise ManageError("internal-error", {})

    def commit(self, message:str = ""):

        if self._not_entered():
            return

        if self._is_default_branch(self.branch):
            return

        if not self._run(self.repodir, git.add, ["."]):
            logger.error(f"Failed to git add local changes")
            raise ManageError("internal-error", {})
        if not self._run(self.repodir, git.commit, ["-m", message]):
            logger.error(f"Failed to git commit local changes")
            raise ManageError("internal-error", {})
        if not self._run(self.repodir, git.push, ["-u", "origin", self.branch]):
            logger.error(f"Failed to git push local changes to remote")
            raise ManageError("internal-error", {})
    
    def __exit__(self, exc_type, exc_value, traceback):

        # Delete the repo we checked out.  
        self._run(self.base_storage_dir, rm, ["-rf", self.repodir])

        self.is_entered = False

    def load_yaml(self, relative_file_path:str) -> dict:

        file_path = Path(self.repodir).joinpath(relative_file_path)
        if file_path.is_file():
            return load_yaml.yaml_file_to_dict(file_path)

        return None

    def write_yaml(self, class_list:list, relative_file_path:str, contents):

        file_path = Path(self.repodir).joinpath(relative_file_path)
        if not file_path.is_file():
            # Try to make the directory, as that at least needs to exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

        load_yaml.class_to_yaml_file(class_list, contents, file_path)

class IndexStorage(GitStorage):

    def __init__(self, config:dict, persist_changes:bool = True):
        super().__init__(config)

        indexstorage_config = config.get("index", {})
        self.index_create_branch_name = indexstorage_config.get("index-create-branch", "create")
        self.persist_changes = persist_changes

        self.entered = False

    def persistChanges(self, value:bool):
        self.persist_changes = value

    def __enter__(self):
        
        if self.entered:
            return self
        self.entered = True        

        super().__enter__()

        super().branch_update(self.index_create_branch_name)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None and self.persist_changes:
            super().commit(f"Updated index file")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False
    

class ThreatModelStorage(GitStorage):

    def __init__(self, config:dict, ID:str):
        super().__init__(config)

        self.ID = ID
        self.entered = False

    
    def __enter__(self):

        if self.entered:
            return self
        self.entered = True

        super().__enter__()

        self.can_commit = False

        # Fetch the directory containing the metadata for the TM ID.  If it doesn't exist, nothing is downloaded
        if not self._run(self.repodir, git, ["sparse-checkout", "set", self.ID]):
            logger.error(f"Could not sparse-checkout directory '{self.ID}'")
            raise ManageError("internal-error", {})

        super().branch_replace(self.ID)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None:
            super().commit(f"Update to {self.ID}")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False

        return False