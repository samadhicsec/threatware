#!/usr/bin/env python3
"""
Classes to use git as a storage repository for threat model metadata
"""
import logging
import os
from pathlib import Path
from io import StringIO
from re import T
from sh.contrib import git
from sh import pushd
from sh import rm
from sh import ErrorReturnCode
import utils.match as match

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
            return True
        return False

    def _run(self, directory, command, *args, out=None):

        #cwd = os.getcwd()
        #os.chdir(dir)

        if out is None:
            out = logger.debug

        with pushd(directory):  
            try:
                logger.debug(f"Running '{command.__name__}' with args '{args}'")
                command(*args, _out=out)
            except ErrorReturnCode as erc:
                logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
            #finally:
            #    os.chdir(cwd)
        

    def __enter__(self):

        buf = StringIO()

        cwd = os.getcwd()
        os.chdir(self.base_storage_dir)

        try:
            logger.debug(f"git clone --no-checkout {self.remote}")
            git.clone("--no-checkout", self.remote, _out=buf, _err_to_out=True)

            outdata = buf.getvalue()
            logger.debug(f"{outdata}")

            # Get the directory where the code was cloned into
            for line in outdata.splitlines():
                if line.startswith("Cloning into '") and line .endswith("'..."):
                    self.repodirname = line.split("'")[1]
                    break

            os.chdir(self.repodirname)
            self.repodir = os.getcwd()

            git("sparse-checkout", "init", "--cone")

        except ErrorReturnCode as erc:
            logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
        finally:
            os.chdir(cwd)

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

        self._run(os.getcwd(), git, ["ls-remote", "--heads", self.remote], out=_check_for_remote_branch)
        
        return remote_branch_exists_var

    def _is_default_branch(self, branch:str):
        if match.is_empty(branch) or match.equals(self.default_branch, branch):
            logger.error(f"Cannot commit directly to default branch")
            return True

        return False

    def branch_update(self, branch:str):
        """ Switches to either a local branch using existing remote branch (fetching any existing changes on that branch), or creates a new local branch """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            self._run(self.repodir, git.checkout, ["-b", self.branch, "origin/" + self.branch], out=logger.debug)
        else:
            self._run(self.repodir, git.checkout, ["-b", self.branch], out=logger.debug)

        # cwd = os.getcwd()
        # os.chdir(self.base_storage_dir)
        # os.chdir(self.repodir)
        # try:
        #     if remote_branch_exists:
        #         git.checkout("-b", self.branch, "origin/" + self.branch, _out=logger.debug)
        #     else:
        #         git.checkout("-b", self.branch, _out=logger.debug)
        # except ErrorReturnCode as erc:
        #     logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
        # finally:
        #     os.chdir(cwd)
    
    def branch_replace(self, branch:str):
        """ Switches to a local branch, deleting any existing remote branch (ignroing any existing changes on that branch) """

        if self._not_entered():
            return

        if self._is_default_branch(branch):
            return

        self.branch = branch

        if self.remote_branch_exists(branch):
            self._run(self.repodir, git.push, ["origin", "-d", self.branch], out=logger.debug)

        self._run(self.repodir, git.checkout, ["-b", self.branch], out=logger.debug)

    def commit(self, message:str = ""):

        if self._not_entered():
            return

        if self._is_default_branch(self.branch):
            return

        cwd = os.getcwd()
        os.chdir(self.base_storage_dir)
        os.chdir(self.repodir)

        try:
            git.add(".", _out=logger.debug)
            git.commit("-m", message, _out=logger.debug)
            git.push("-u", "origin", self.branch, _out=logger.debug)
        except ErrorReturnCode as erc:
            logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and output '{erc.stdout}'")
        finally:
            os.chdir(cwd)
    
    def __exit__(self, exc_type, exc_value, traceback):

        cwd = os.getcwd()
        os.chdir(self.base_storage_dir)

        rm("-rf", self.repodir)

        os.chdir(cwd)

        self.is_entered = False


class IndexStorage(GitStorage):

    def __init__(self, config:dict):
        super().__init__(config)

        indexstorage_config = config.get("index", {})
        self.index_create_branch_name = indexstorage_config.get("index-create-branch", "create")

        #self.metadata_filename = config.get("metadata-filename", "threatmodels.yaml")
        self.entered = False
        
    def __enter__(self):
        
        if self.entered:
            return self
        self.entered = True        

        super().__enter__(self)

        self.can_commit = False

        #threatmodels = load_yaml.yaml_file_to_dict(self.metadata_filename)

        #self.metadata = {}
        #for TMid, TMentry in threatmodels["threatmodels"].items():
        #    self.metadata[TMid] = MetadataIndexEntry(TMentry)

        super().branch_update(self.index_create_branch_name)

        return self

    def __exit__(self, exc_type, exc_value, traceback):

        if exc_type is None:
            super().commit(f"Updated index file")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False

    #def getIndexEntry(self, ID:str):
    #    return self.metadata.get(ID, None)

    #def setEntry(self, ID:str, entry:MetadataIndexEntry):
    #    self.metadata[ID] = entry

    #def getIndexEntryByLocation(self, location:str):

    #    for keyvalue, entryvalue in self.metadata.items():
    #        if match.equals(location, entryvalue.location):
    #            return entryvalue

    #    return None

    

class ThreatModelStorage(GitStorage):

    def __init__(self, config:dict, ID:str):
        super().__init__(config)

        self.ID = ID
        #self.metadata_file = Path.joinpath(self.repodir, self.ID, config["metadata-filename"])
        #self.metadata_dict = load_yaml.yaml_file_to_dict(self.metadata_file)
        self.entered = False

    
    def __enter__(self):

        if self.entered:
            return self
        self.entered = True

        super().__enter__()

        self.can_commit = False

        # Fetch the directory containing the metadata for the TM ID.  If it doesn't exist, nothing is downloaded
        self._run(self.repodir, git, ["sparse-checkout", "set", self.ID])

        # Does the dir exist?
        #if not Path.joinpath(self.repodir, self.ID).is_dir():
        #    self.tm_metadata = ThreatModelMetaData.skeleton(self.ID)
        #else:
        #    self.tm_metadata = ThreatModelMetaData(self.metadata_dict)

        super().branch_replace(self.ID)

        return self

    #def getMetadata(self):
    #    return self.tm_metadata

    def __exit__(self, exc_type, exc_value, traceback):

        #if self.can_commit:
        if exc_type is None:
            super().commit(f"Update to {self.ID}")

        super().__exit__(exc_type, exc_value, traceback)

        self.entered = False

        return False