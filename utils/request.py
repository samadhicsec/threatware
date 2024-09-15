import logging
import utils.logging

utils.logging.configureLogging()
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class Request:

    action:str
    scheme:str
    docloc:str
    doctemplate:str
    ID:str
    IDprefix:str
    lang:str
    format:str
    meta:str
    reports:str

    @classmethod
    def set(cls, request_parameters:dict) -> None:
        
        # Store the query string parameters
        cls.action = request_parameters.get("action", None)
        cls.scheme = request_parameters.get("scheme", None)
        cls.docloc = request_parameters.get("docloc", None)
        cls.doctemplate = request_parameters.get("doctemplate", None)
        cls.ID = request_parameters.get("ID", None)
        cls.IDprefix = request_parameters.get("IDprefix", None)
        cls.lang = request_parameters.get("lang", None)
        cls.format = request_parameters.get("format", "json")
        cls.meta = request_parameters.get("meta", "tags")
        cls.reports = request_parameters.get("reports", "none")

        logger.info(f"Threatware called with parameters = '{ request_parameters }'")

    @classmethod
    def get(cls) -> dict:
        return {
            "action": cls.action,
            "scheme": cls.scheme,
            "docloc": cls.docloc,
            "doctemplate": cls.doctemplate,
            "ID": cls.ID,
            "IDprefix": cls.IDprefix,
            "lang": cls.lang,
            "format": cls.format,
            "meta": cls.meta,
            "reports": cls.reports
        }