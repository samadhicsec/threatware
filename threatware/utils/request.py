import logging
import threatware.utils.logging

threatware.utils.logging.configureLogging()
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

class Request:

    action:str
    scheme:str
    docloc:str
    document:str
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
        cls.document = request_parameters.get("document", None)
        cls.doctemplate = request_parameters.get("doctemplate", None)
        cls.template = request_parameters.get("template", None)
        cls.ID = request_parameters.get("ID", None)
        cls.IDprefix = request_parameters.get("IDprefix", None)
        cls.lang = request_parameters.get("lang", None)
        cls.format = request_parameters.get("format", "json")
        cls.meta = request_parameters.get("meta", "tags")
        cls.reports = request_parameters.get("reports", "none")

        # Create a copy without document or template as it may be large
        request_parameters_no_document = request_parameters.copy()
        if "document" in request_parameters_no_document:
            request_parameters_no_document["document"] = "<omitted>"
        if "template" in request_parameters_no_document:
            request_parameters_no_document["template"] = "<omitted>"

        logger.info(f"Threatware called with parameters = '{ request_parameters_no_document }'")

    @classmethod
    def get(cls) -> dict:
        return {
            "action": cls.action,
            "scheme": cls.scheme,
            "docloc": cls.docloc,
            "document": "<omitted>" if cls.document is not None else None,
            "doctemplate": cls.doctemplate,
            "template": "<omitted>" if cls.template is not None else None,
            "ID": cls.ID,
            "IDprefix": cls.IDprefix,
            "lang": cls.lang,
            "format": cls.format,
            "meta": cls.meta,
            "reports": cls.reports
        }

    @classmethod
    def isAPIFormat(cls) -> bool:
        return cls.format in ["json", "yaml"]