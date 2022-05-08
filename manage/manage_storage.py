#!/usr/bin/env python3
"""
Classes to use git as a storage repository for threat model metadata
"""
import logging
from storage.gitrepo import GitStorage
import utils.match as match
from language.translate import Translate

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))


class IndexStorage(GitStorage):

    def __init__(self, config:dict, execution_env, persist_changes:bool = True, output_texts:dict = {}):
        super().__init__(config, execution_env)

        indexstorage_config = config.get("index", {})
        self.index_create_branch_name = indexstorage_config.get("index-create-branch", "create")
        self.output_texts = output_texts
        self.commit_message_key = indexstorage_config.get("index-commit-message-text-key")
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
            if match.is_empty((commit_message := Translate.localise(self.output_texts, self.commit_message_key))):
                # Always have a default
                commit_message = f"Updated index file"
            super().commit(commit_message)

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False
    

class ThreatModelStorage(GitStorage):

    def __init__(self, config:dict, execution_env, ID:str, persist_changes:bool = True, output_texts:dict = {}):
        super().__init__(config, execution_env)

        tm_storage_config = config.get("threatmodel", {})
        self.ID = ID
        self.entered = False
        self.output_texts = output_texts
        self.commit_message_key = tm_storage_config.get("tm-commit-message-text-key")
        self.persist_changes = persist_changes

    
    def __enter__(self):

        if self.entered:
            return self
        self.entered = True

        super().__enter__()

        self.can_commit = False

        # Fetch the directory containing the metadata for the TM ID.  If it doesn't exist, nothing is downloaded
        super().checkout_directory(self.ID)

        # Overwrite any existing branch for making changes
        super().branch_replace(self.ID)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None and self.persist_changes:
            if match.is_empty((commit_message := Translate.localise(self.output_texts, self.commit_message_key, {"ID":self.ID}))):
                # Always have a default
                commit_message = f"Update to {self.ID}"
            super().commit(commit_message)

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False

        return False