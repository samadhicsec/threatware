import logging
import base64

import threatware.utils.logging
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

class Location:

    docloc:str
    b64document:str

    def __init__(self, docloc:str=None, b64document:str=None) -> None:
        self.docloc = docloc
        self.b64document = b64document

    def isLocationIDProvided(self) -> bool:
        return self.docloc is not None
    
    def getLocationID(self) -> str:
        return self.docloc

    def isDocumentProvided(self) -> bool:
        return self.b64document is not None

    def getDocument(self) -> str:
        '''
        Although the Base64 version of the document is passed into the constructor, this method returns the raw document string.
        
        :param self: Description
        :return: The raw (non-Base64) version of the document
        :rtype: str
        '''
        # Decode the document from Base64 and return it
        
        return base64.b64decode(self.b64document).decode('utf-8')