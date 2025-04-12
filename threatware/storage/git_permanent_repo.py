#!/usr/bin/env python3
"""
Class to download a git repo
"""
import logging
from io import StringIO
from threatware.storage.gitrepo import GitStorage
import threatware.utils.match as match
import threatware.utils.shell as shell
from sh import git
from threatware.utils.error import StorageError

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

class GitPermanentStorage(GitStorage):

    is_entered = True

    def __init__(self, config:dict, execution_env):

        super().__init__(config, execution_env)

        self.is_entered = True

    def clone(self, target_dir:str, branch:str):

        buf = StringIO()
        
        #if Path(self.repodir).is_dir():
        #    logger.warning(f"Directory '{self.repodir}' already exists")

        if match.is_empty(branch):
            git_args = ["--depth", "1", self.remote, target_dir]
        else:
            git_args = ["--depth", "1", "--branch", branch, self.remote, target_dir]

        # Must be set for any git usage
        shell.global_kwargs["_tty_out"] = False

        if not shell.run(self.base_storage_dir, git.clone, git_args, _out=buf, _err_to_out=True):
            outdata = buf.getvalue()
            logger.error(f"Could not clone repo '{self.remote}'.  Error message: {outdata}")
            raise StorageError("storage.clone-error", {"storage":{"remote":self.remote}})

