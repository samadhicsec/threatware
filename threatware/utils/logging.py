#!/usr/bin/env python3

import os
import logging

LOGGERNAME = 'threatware'

def getLoggerName(name):

    return LOGGERNAME + '.' + name

def configureLogging():

    # create logger
    logger = logging.getLogger(LOGGERNAME)
    
    #log_level = logging.DEBUG
    log_level = logging.WARNING

    if (env_log_level_str := os.getenv("THREATWARE_LOG_LEVEL")) is not None:
        env_log_level = logging.getLevelName(env_log_level_str)
        if isinstance(env_log_level, int):
            log_level = env_log_level
    
    logger.setLevel(log_level)

    logger.propagate = False

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(funcName)s:%(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    