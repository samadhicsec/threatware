#!/usr/bin/env python3
"""
Handler to invoke verifier
"""

import logging
import sys
import argparse
import configparser
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
from threatware.utils.error import ThreatwareError
from threatware.utils.request import Request
from threatware.utils.location import Location
from threatware.utils.config import ConfigBase
from threatware.utils.output import FormatOutput
import threatware.utils.logging
from threatware.providers import provider
from threatware.language.translate import Translate
from threatware.schemes.schemes import load_scheme, get_default_scheme, get_default_template
import threatware.actions.convert as convert
import threatware.actions.verify as verify
import threatware.actions.manage as manage
import threatware.actions.measure as measure
from threatware.utils.output import FormatOutput, OutputType
from threatware.response.response import Response

threatware.utils.logging.configureLogging()
logger = logging.getLogger(threatware.utils.logging.getLoggerName(__name__))

HANDLER_TEXTS_YAML = "handler_texts.yaml"
HANDLER_TEXTS_YAML_PATH = str(Path(__file__).absolute().parent.joinpath(HANDLER_TEXTS_YAML))

ACTION_CONVERT = 'convert'
ACTION_VERIFY = 'verify'
ACTION_MANAGE_INDEXDATA = 'manage.indexdata'
ACTION_MANAGE_CREATE = 'manage.create'
ACTION_MANAGE_SUBMIT = 'manage.submit'
ACTION_MANAGE_CHECK = 'manage.check'
ACTION_MEASURE = 'measure'

def lambda_handler(event, context):

    # Fitler the set of query string parameters to just ones we know about
    if (qsp := event.get("queryStringParameters", {})) is None:
        qsp = {}
    Request.set(qsp)

    # Very first thing we need to do is find where all the configuration files are, and if they are not already present, download them.
    # How we do that depends what env we are in.  Providers usually take a config file, but we don't have them yet, so load without config (which limits what methods we can use)
    if getattr(context, "threatware.cli", False):
        execution_env = provider.get_provider("cli", no_config_mode=True)
    elif getattr(context, "threatware.api", False):
        execution_env = provider.get_provider("api", no_config_mode=True)
    else:
        # We are being called as a lambda, so get credentials from cloud
        execution_env = provider.get_provider("aws.lambda", no_config_mode=True)
    
    try:
        
        # This will set the ConfigBase.base_dir value so we can load config from this directory
        try:
            ConfigBase.init(execution_env)
        
        finally:
            # ConfigBase.init is guaranteed to configure at least the built-in config, which is enough to display at least an error.  Any exception in ConfigBase.init will
            # be captured by the outer try, but Translate/FormatOutput will be sufficiently configured in this finally: block to allow a properly formatted error message to
            # be returned to the user.

            ###
            # Now we can load things that have dynamic configuration
            ###

            # We need this to support localisation of keywords
            Translate.init()

            # Load the texts file with localised error messages
            handler_output = FormatOutput({"template-text-file":ConfigBase.getConfigPath(HANDLER_TEXTS_YAML_PATH)})
            # Create a response in case of an unexpected error
            response = Response(handler_output)
    

        # Validate input

        if response.getFormat() == "html":      # The Response object will get the appropriate format to validate, as it may be a parameter or from config
            if Request.action not in [ACTION_VERIFY]:
                Request.format = "json"     # Future Response objects will use this new value for format
                logger.warning(f"'html' format is only supported for the 'verify' action, defaulting format to 'json'")
            if Request.reports != "none":
                Request.reports = "none"
                logger.warning(f"Additional reports are not supported in 'html' format, defaulting reports to 'none'")

        if Request.action is None:
            logger.error("action is a mandatory parameter")
            handler_output.setError("action-is-mandatory", {})
            response = Response(handler_output)
        elif Request.action not in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]:
            logger.error(f"the action parameter must be one of {[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]}")
            handler_output.setError("action-value", {"actions":[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]})
            response = Response(handler_output)
        # elif Request.action in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and Request.scheme is None:
        #     logger.error("scheme is a mandatory parameter")
        #     handler_output.setError("scheme-is-mandatory", {})
        #     response = Response(handler_output)
        elif Request.action in [ACTION_CONVERT, ACTION_VERIFY] and Request.document is None and Request.docloc is None:
            logger.error("Either document or docloc is a mandatory parameter")
            handler_output.setError("document-or-docloc-mandatory", {})
            response = Response(handler_output)
        elif Request.action in [ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and Request.docloc is None:
            logger.error("docloc is a mandatory parameter")
            handler_output.setError("docloc-is-mandatory", {})
            response = Response(handler_output)
        # elif Request.action in [ACTION_VERIFY, ACTION_MEASURE] and  Request.doctemplate is None:
        #     logger.error(f"doctemplate is a mandatory parameter when action = {Request.action}")
        #     handler_output.setError("doctemplate-is-mandatory", {"action":Request.action})
        #     response = Response(handler_output)
        elif Request.action in [ACTION_MANAGE_INDEXDATA] and id is None:
            logger.error(f"ID is a mandatory parameter when action = {Request.action}")
            handler_output.setError("id-is-mandatory", {"action":Request.action})
            response = Response(handler_output)
        elif Request.action in [ACTION_MANAGE_CREATE] and Request.IDprefix is None:
            logger.error(f"IDprefix is a mandatory parameter when action = {Request.action}")
            handler_output.setError("idprefix-is-mandatory", {"action":Request.action})
            response = Response(handler_output)

        else:
            # Load the execution environment again, as this time we have configuration files to enable full functionality
            if getattr(context, "threatware.cli", False):
                # Get creds locally
                execution_env = provider.get_provider("cli")
            elif getattr(context, "threatware.api", False):
                execution_env = provider.get_provider("api")
            else:
                # We are being called as a lambda, so get credentials from cloud
                execution_env = provider.get_provider("aws.lambda")

            if Request.scheme is None:
                Request.scheme = get_default_scheme()
            if Request.scheme is not None:
                schemeDict = load_scheme(Request.scheme)
            
            if Request.action in [ACTION_VERIFY, ACTION_MEASURE] and Request.doctemplate is None:
                Request.doctemplate = get_default_template(schemeDict)

            if Request.action == ACTION_CONVERT:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, Location(Request.docloc, Request.document), schemeDict)
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()

                    verify_config = verify.config(schemeDict)

                    # Convert output is much more useful if it contains the default verify tags as well
                    # This will update the model in place
                    verify.assign_default_tags(verify_config, doc_model)

                response = Response(convert_output, Request.meta)

            elif Request.action == ACTION_VERIFY:

                convert_config = convert.config()
                
                # Convert the TM template
                convert_output = convert.convert_template(convert_config, execution_env, schemeDict, Location(Request.doctemplate, Request.template))
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    template_model = convert_output.getDetails()

                    # Convert the TM document
                    convert_output = convert.convert(convert_config, execution_env, schemeDict, Location(Request.docloc, Request.document))
                    response = Response(convert_output, force_api_format=True)     # In case convert failed

                    if convert_output.getResult() != OutputType.ERROR:

                        doc_model = convert_output.getDetails()

                        verify_config = verify.config(schemeDict)

                        # Verify the TM document
                        verify_output = verify.verify(verify_config, doc_model, template_model)
                        response = Response(verify_output, force_api_format=True)     # In case verify failed

                        if verify_output.getResult() != OutputType.ERROR:
                            
                            issues = verify_output.getDetails()

                            # Generate a report on verification issues and analysis
                            verify_output = verify.report(verify_config, doc_model, issues, Request.reports)

                            response = Response(verify_output)

            elif Request.action == ACTION_MANAGE_INDEXDATA:
                
                manage_config = manage.config()

                output = manage.indexdata(manage_config, execution_env, Request.ID)

                response = Response(output)

            elif Request.action == ACTION_MANAGE_CREATE:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, schemeDict, Location(Request.docloc))
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()

                    manage_config = manage.config()

                    output = manage.create(manage_config, execution_env, Request.IDprefix, Request.scheme, Request.docloc, doc_model)

                    response = Response(output)

            elif Request.action == ACTION_MANAGE_CHECK:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, schemeDict, Location(Request.docloc))
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()
                
                    manage_config = manage.config()

                    # 'check' relies on measure
                    measure_config = measure.config()

                    output = manage.check(manage_config, execution_env, Request.docloc, Request.scheme, doc_model, measure_config, measure.distance)

                    response = Response(output)
            
            elif Request.action == ACTION_MANAGE_SUBMIT:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, schemeDict, Location(Request.docloc))
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()

                    manage_config = manage.config()

                    output = manage.submit(manage_config, execution_env, Request.docloc, Request.scheme, doc_model)

                    response = Response(output, "none")

            elif Request.action == ACTION_MEASURE:

                convert_config = convert.config()

                # Convert the TM template
                convert_output = convert.convert_template(convert_config, execution_env, schemeDict, Location(Request.doctemplate))
                response = Response(convert_output, force_api_format=True)     # In case convert failed

                if convert_output.getResult() != OutputType.ERROR:

                    template_model = convert_output.getDetails()

                    # Convert the TM document
                    convert_output = convert.convert(convert_config, execution_env, schemeDict, Location(Request.docloc))
                    response = Response(convert_output)     # In case convert failed

                    if convert_output.getResult() != OutputType.ERROR:

                        doc_model = convert_output.getDetails()

                        measure_config = measure.config()
                        
                        output = measure.distance_to_template(measure_config, execution_env, doc_model, template_model)

                        response = Response(output)
    
    except Exception as e:
        logger.error(e)
        if issubclass(type(e), ThreatwareError):
            handler_output.setError(e.text_key, e.template_values)
        else:
            handler_output.setError("internal-error", {})
        response = Response(handler_output, force_api_format=True)

    # Respond
    return {
        'statusCode': 200,
        "headers": response.getHeaders(),
        'body': response.getBody()
    }

def getVersion(prog):

    # This will search sys.path for threatware.egg-info/.dist-info directory to get the version from the PKG-INFO file
    try:
        
        version_number = version(prog)

        return version_number

    except PackageNotFoundError:
        pass

    # If the above fails then get the version from the local setup.cfg file
    setup_config_parser = configparser.ConfigParser()
    setup_config_parser.read(str(Path(__file__).absolute().parent.parent.joinpath("setup.cfg")))
    setup_config_dict = dict(setup_config_parser.items("metadata"))
    if "version" in setup_config_dict:
        return setup_config_dict["version"]

    return None

def main():

    scheme_help = 'Identifier for the threat model scheme (which contains location information).  If not provided, the first entry in config schemes/schemes.yaml will be used as the default scheme.'
    docloc_help = 'Location identifier of the document'
    document_help = 'Base64 encoded document.  If no value is provided, the document will be read from stdin.'
    template_help = 'Identifier for the document template (overrides template in scheme).  If not provided, the template defined in the scheme will be used.'
    reports_help = "Additional reports can be returned with more information.\n'assets' will show the controls covering each asset per (in-scope) storage location.\n'controls' will show which assets each control covers per (in-scope) storage location"

    parser = argparse.ArgumentParser(prog='threatware', description='Threatware is a tool to help review threat models and provide a process to manage threat models.  It works directly with threat models as Confluence/Google Docs documents.  For detailed help on deployment, configuration and customisation, see https://threatware.readthedocs.io')

    version_str = f"{parser.prog} v{getVersion(parser.prog)}"
    parser.add_argument("-v", "--version", action="version", version=version_str)
    parser.add_argument("-l", "--lang", required=False, help="Language code for output texts")
    parser.add_argument("-f", "--format", required=False, help="Format for output, either JSON, YAML or HTML (verify only)", choices=['json', 'yaml', 'html'])

    subparsers = parser.add_subparsers(dest="action", required=True)

    # convert
    parser_convert = subparsers.add_parser("convert", help='Convert a threat model for analysis')
    parser_convert.add_argument('-s', '--scheme', required=False, help=scheme_help)
    docloc_group = parser_convert.add_mutually_exclusive_group(required=True)
    docloc_group.add_argument('-d', '--docloc', help=docloc_help)
    docloc_group.add_argument('-i', '--document', nargs='?', const='STDIN', help=document_help)
    #parser_convert.add_argument('-d', '--docloc', required=True, help=doc_help)
    parser_convert.add_argument("-m", "--meta", required=False, help="What level of meta data about fields should be returned.  Note, 'properties' returns 'tags' as well.", default="tags", choices=['none', 'tags', 'properties'])

    # verify
    parser_verify = subparsers.add_parser("verify", help='Verify a threat model is ready to be submitted for approval', formatter_class=argparse.RawTextHelpFormatter)
    parser_verify.add_argument('-s', '--scheme', required=False, help=scheme_help)
    parser_verify.add_argument('-d', '--docloc', required=True, help=docloc_help)
    parser_verify.add_argument('-t', '--doctemplate', required=False, help=template_help)
    parser_verify.add_argument("-r", "--reports", required=False, help=reports_help, default='none', choices=['none', 'assets', 'controls', 'all'])

    # manage
    parser_manage = subparsers.add_parser("manage", help='Manage the status of threat models')
    manage_subparsers = parser_manage.add_subparsers(dest="manage_command", required=True)
    # manage.indexdata
    parser_manage_indexdata = manage_subparsers.add_parser("indexdata", help='Get the threat model index metadata for a threat model')
    parser_manage_indexdata.add_argument('-id', required=True, help='The document ID for the threat model index metadata to return')
    # manage.createdata
    parser_manage_create = manage_subparsers.add_parser("create", help='Create a new document ID for a new threat model')
    parser_manage_create.add_argument('-idprefix', required=True, help='The prefix of the document ID e.g. "CMP.TMD"')
    parser_manage_create.add_argument('-s', '--scheme', required=False, help=scheme_help)
    parser_manage_create.add_argument('-d', '--docloc', required=True, help=docloc_help)
    # manage.check
    parser_manage_check = manage_subparsers.add_parser("check", help='Check whether the current threat model requires re-approval')
    parser_manage_check.add_argument('-s', '--scheme', required=False, help=scheme_help)
    parser_manage_check.add_argument('-d', '--docloc', required=True, help=docloc_help)
    # manage.submit
    parser_manage_submit = manage_subparsers.add_parser("submit", help='Submit a threat model for approval')
    parser_manage_submit.add_argument('-s', '--scheme', required=False, help=scheme_help)
    parser_manage_submit.add_argument('-d', '--docloc', required=True, help=docloc_help)
    
    # measure
    parser_measure = subparsers.add_parser("measure", help='Measure the distance of a TM from its template')
    parser_measure.add_argument('-s', '--scheme', required=False, help=scheme_help)
    parser_measure.add_argument('-d', '--docloc', required=True, help=docloc_help)
    parser_measure.add_argument('-t', '--doctemplate', required=False, help=template_help)

    args = parser.parse_args()

    # Print out version string for the logs.  Do it after we parse the args so we don't print it twice if run with --version
    print(version_str, file=sys.stderr)

    # Build input for handler
    event ={}

    class Object(object):
        pass
    context = Object()
    setattr(context, "threatware.cli", True)

    action = args.action
    if action == "manage":
        action = action + "." + args.manage_command

    event["queryStringParameters"] = {}
    event["queryStringParameters"]["lang"] = args.lang if "lang" in args else None
    event["queryStringParameters"]["format"] = args.format if "format" in args else None
    event["queryStringParameters"]["action"] = action
    event["queryStringParameters"]["scheme"] = args.scheme if "scheme" in args else None
    event["queryStringParameters"]["docloc"] = args.docloc if "docloc" in args else None
    if (args.document is None or args.document == 'STDIN') and not sys.stdin.isatty():
        # Read document from stdin
        document_b64 = sys.stdin.read()
        event["queryStringParameters"]["document"] = document_b64
    else:
        event["queryStringParameters"]["document"] = args.document if "document" in args else None
    event["queryStringParameters"]["meta"] = args.meta if "meta" in args else None
    event["queryStringParameters"]["doctemplate"] = args.doctemplate if "doctemplate" in args else None
    event["queryStringParameters"]["ID"] = args.id if "id" in args else None
    event["queryStringParameters"]["IDprefix"] = args.idprefix if "idprefix" in args else None
    event["queryStringParameters"]["reports"] = args.reports if "reports" in args else None

    response = lambda_handler(event, context)

    print(response["body"])

    return 


if __name__ == "__main__":
    sys.exit(main())