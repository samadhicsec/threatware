import logging

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))


class CreateConfig:

    def __init__(self, config:dict):
        self.config = config

    def getDefaultIDPrefix(self) -> str:
        return self.config.get("create", {}).get("default-IDprefix", "")