#!/usr/bin/env python3
"""
Run shell commands
"""

import logging
from sh import pushd
from sh import ErrorReturnCode

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

def run(directory, command, *args, **kwargs):
    """
    Run a shell command using the sh package

    Generically runs a sh command, with logging, and captures output as specified

    Parameters
    ----------
    directory : str
        The directory where to execute the command
    command 
        The sh command to execute
    *args : list
        The args to pass to the command
    **kwargs : list
        The named args to pass to the command.  Use "_out" named argument to specify output (se sh package)

    Returns
    -------
    bool : True if no errors occurred, False otherwise
    """

    if "_out" not in kwargs:
        kwargs["_out"] = logger.debug

    if "_close_fds" not in kwargs:
        # To work in lambda which doesn't have '/dev/fd' (which this argument that defaults to true relies on), we need to set this to False.  Hope this has no negative side effects
        kwargs["_close_fds"] = False

    with pushd(directory):  
        try:
            logger.debug(f"Running '{command.__name__}' with args '{args}' in directory {directory}")
            command(*args, **kwargs)
        except ErrorReturnCode as erc:
            try:
                stdout_data = erc.stdout.decode()
                stderr_data = erc.stderr.decode()
            except (UnicodeDecodeError, AttributeError):
                pass

            logger.error(f"'{erc.full_cmd}' failed with exit code '{erc.exit_code}' and stdout '{stdout_data}' and stderr '{stderr_data}'")
            return False

    return True        

    