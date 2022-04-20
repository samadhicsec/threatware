#!/usr/bin/env python3
"""
Classes to use git as a storage repository for threat model metadata
"""
import logging
from storage.gitrepo import GitStorage
import utils.shell as shell
from sh.contrib import git
from utils.error import ManageError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


class IndexStorage(GitStorage):

    def __init__(self, config:dict, execution_env, persist_changes:bool = True):
        super().__init__(config, execution_env)

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

        # Need to check if the remote branch has been merged i.e. git branch -r --merged approved, if so create a new branch
        # Once create branch merged the official approved branch may have been changed, so we need to us that, as opposed to the old create branch.  This
        # can still happen if the create branch has not been updated, but someone will be merging at some stage and can review
        if super().is_merged_to_default(self.index_create_branch_name):
            super().branch_replace(self.index_create_branch_name)
        else:
            super().branch_update(self.index_create_branch_name)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None and self.persist_changes:
            super().commit(f"Updated index file")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False
    

class ThreatModelStorage(GitStorage):

    def __init__(self, config:dict, execution_env, ID:str, persist_changes:bool = True):
        super().__init__(config, execution_env)

        self.ID = ID
        self.entered = False
        self.persist_changes = persist_changes

    
    def __enter__(self):

        if self.entered:
            return self
        self.entered = True

        super().__enter__()

        self.can_commit = False

        # Fetch the directory containing the metadata for the TM ID.  If it doesn't exist, nothing is downloaded
        if not shell.run(self.repodir, git, ["sparse-checkout", "add", self.ID]):
            logger.error(f"Could not sparse-checkout directory '{self.ID}'")
            raise ManageError("internal-error", {})

        super().branch_replace(self.ID)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None and self.persist_changes:
            super().commit(f"Update to {self.ID}")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False

        return False