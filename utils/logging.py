#!/usr/bin/env python3

import logging

LOGGERNAME = 'threatware'

def getLoggerName(name):

    return LOGGERNAME + '.' + name

def configureLogging():

    # create logger
    logger = logging.getLogger(LOGGERNAME)
    #logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.WARNING)
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
    