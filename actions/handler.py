#!/usr/bin/env python3
"""
Handler to invoke verifier
"""

import logging
import sys
import argparse
import json
from pathlib import Path
from storage.gitrepo import GitStorage
from utils.error import ThreatwareError
from utils.config import ConfigBase
from utils.output import FormatOutput
import utils.logging
from providers import provider
from language.translate import Translate
from schemes.schemes import load_scheme
import actions.convert as convert
import actions.verify as verify
import actions.manage as manage
import actions.measure as measure
from utils.output import FormatOutput, OutputType
from data.key import key as Key

utils.logging.configureLogging()
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

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
    qsp = event.get("queryStringParameters", {})
    filtered_qsp = {"request":{}}
    if (action := qsp.get("action", None)) is not None:
        filtered_qsp["request"]["action"] = action
    if (schemeID := qsp.get("scheme", None)) is not None:
        filtered_qsp["request"]["scheme"] = schemeID
    if (docloc := qsp.get("docloc", None)) is not None:
        filtered_qsp["request"]["docloc"] = docloc
    if (doctemplate := qsp.get("doctemplate", None)) is not None:
        filtered_qsp["request"]["doctemplate"] = doctemplate
    if (id := qsp.get("ID", None)) is not None:
        filtered_qsp["request"]["ID"] = id
    if (IDprefix := qsp.get("IDprefix", None)) is not None:
        filtered_qsp["request"]["IDprefix"] = IDprefix
    if (lang := qsp.get("lang", None)) is not None:
        filtered_qsp["request"]["lang"] = lang
    if (output_format := qsp.get("format", None)) is not None:
        filtered_qsp["request"]["format"] = output_format
    if (convert_meta := qsp.get("meta", None)) is not None:
        filtered_qsp["request"]["meta"] = convert_meta

    logger.info(f"Threatware called with parameters = '{ filtered_qsp['request'] }'")

    # Very first thing we need to do is find where all the configuration files are, and if they are not already present, download them.
    # How we do that depends what env we are in.  Providers usually take a config file, but we don't have them yet, so load without config (which limits what methods we can use)
    if getattr(context, "threatware.cli", False):
        execution_env = provider.get_provider("cli", no_config_mode=True)
    else:
        GitStorage.containerised = True
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
            Translate.init(lang, filtered_qsp)

            # Determine output Content-Type
            if "format" in filtered_qsp["request"] and filtered_qsp["request"]["format"].lower() in ["json", "yaml"]:
                FormatOutput.output_format = filtered_qsp["request"]["format"].lower()
            content_type = "application/json"

            # We can treat the parameters as static
            FormatOutput.request_parameters = filtered_qsp

            # Load the texts file with localised error messages
            handler_output = FormatOutput({"template-text-file":ConfigBase.getConfigPath(HANDLER_TEXTS_YAML_PATH)})

    

        # Validate input
        if action is None:
            logger.error("action is a mandatory parameter")
            handler_output.setError("action-is-mandatory", {})
            content_type, body = handler_output.getContent()
        elif action not in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]:
            logger.error(f"the action parameter must be one of {[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]}")
            handler_output.setError("action-value", {"actions":[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_INDEXDATA, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE]})
            content_type, body = handler_output.getContent()
        elif action in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and schemeID is None:
            logger.error("scheme is a mandatory parameter")
            handler_output.setError("scheme-is-mandatory", {})
            content_type, body = handler_output.getContent()
        elif action in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and docloc is None:
            logger.error("docloc is a mandatory parameter")
            handler_output.setError("docloc-is-mandatory", {})
            content_type, body = handler_output.getContent()
        elif action in [ACTION_VERIFY, ACTION_MEASURE] and  doctemplate is None:
            logger.error(f"doctemplate is a mandatory parameter when action = {action}")
            handler_output.setError("doctemplate-is-mandatory", {"action":action})
            content_type, body = handler_output.getContent()
        elif action in [ACTION_MANAGE_INDEXDATA] and id is None:
            logger.error(f"ID is a mandatory parameter when action = {action}")
            handler_output.setError("id-is-mandatory", {"action":action})
            content_type, body = handler_output.getContent()
        elif action in [ACTION_MANAGE_CREATE] and IDprefix is None:
            logger.error(f"IDprefix is a mandatory parameter when action = {action}")
            handler_output.setError("idprefix-is-mandatory", {"action":action})
            content_type, body = handler_output.getContent()

        else:
            # Load the execution environment again, as this time we have configuration files to enable full functionality
            if getattr(context, "threatware.cli", False):
                # Get creds locally
                execution_env = provider.get_provider("cli")
            else:
                GitStorage.containerised = True
                # We are being called as a lambda, so get credentials from cloud
                execution_env = provider.get_provider("aws.lambda")
                #execution_env = provider.get_provider("cli")

            if schemeID is not None:
                schemeDict = load_scheme(schemeID)

            if action == ACTION_CONVERT:
                
                convert_config = convert.config()

                # Convert the TM document
                output = convert.convert(convert_config, execution_env, schemeDict, docloc)

                content_type, body = output.getContent(lambda : Key.config_serialisation(convert_meta))

            elif action == ACTION_VERIFY:

                convert_config = convert.config()
                
                # Convert the TM template
                convert_output = convert.convert_template(convert_config, execution_env, schemeDict, doctemplate)
                content_type, body = convert_output.getContent()

                if convert_output.getResult() != OutputType.ERROR:

                    template_model = convert_output.getDetails()

                    # Convert the TM document
                    convert_output = convert.convert(convert_config, execution_env, schemeDict, docloc)
                    content_type, body = convert_output.getContent()

                    if convert_output.getResult() != OutputType.ERROR:

                        doc_model = convert_output.getDetails()

                        verify_config = verify.config(schemeDict)

                        # Verify the TM document
                        verify_output = verify.verify(verify_config, doc_model, template_model)
                        content_type, body = verify_output.getContent()

                        if verify_output.getResult() != OutputType.ERROR:
                            
                            issues = verify_output.getDetails()

                            # Generate a report on verification issues and analysis
                            verify_output = verify.report(verify_config, doc_model, issues)

                            #body = verify_output.tojson()
                            content_type, body = verify_output.getContent()

            elif action == ACTION_MANAGE_INDEXDATA:
                
                manage_config = manage.config()

                output = manage.indexdata(manage_config, execution_env, id)

                content_type, body = output.getContent()

            elif action == ACTION_MANAGE_CREATE:
                
                manage_config = manage.config()

                output = manage.create(manage_config, execution_env, IDprefix, schemeID, docloc)

                content_type, body = output.getContent()

            elif action == ACTION_MANAGE_CHECK:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, schemeDict, docloc)
                content_type, body = convert_output.getContent()

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()
                
                    manage_config = manage.config()

                    # 'check' relies on measure
                    measure_config = measure.config()

                    output = manage.check(manage_config, execution_env, docloc, schemeID, doc_model, measure_config, measure.distance)

                    content_type, body = output.getContent()
            
            elif action == ACTION_MANAGE_SUBMIT:
                
                convert_config = convert.config()

                # Convert the TM document
                convert_output = convert.convert(convert_config, execution_env, schemeDict, docloc)
                content_type, body = convert_output.getContent()

                if convert_output.getResult() != OutputType.ERROR:

                    doc_model = convert_output.getDetails()

                    manage_config = manage.config()

                    output = manage.submit(manage_config, execution_env, docloc, schemeID, doc_model)

                    content_type, body = output.getContent()

            elif action == ACTION_MEASURE:

                convert_config = convert.config()

                # Convert the TM template
                convert_output = convert.convert_template(convert_config, execution_env, schemeDict, doctemplate)
                content_type, body = convert_output.getContent()

                if convert_output.getResult() != OutputType.ERROR:

                    template_model = convert_output.getDetails()

                    # Convert the TM document
                    convert_output = convert.convert(convert_config, execution_env, schemeDict, docloc)
                    content_type, body = convert_output.getContent()

                    if convert_output.getResult() != OutputType.ERROR:

                        doc_model = convert_output.getDetails()

                        measure_config = measure.config()
                        
                        output = measure.distance_to_template(measure_config, execution_env, doc_model, template_model)

                        content_type, body = output.getContent()
    
    except Exception as e:
        logger.error(e)
        if issubclass(type(e), ThreatwareError):
            handler_output.setError(e.text_key, e.template_values)
        else:
            handler_output.setError("internal-error", {})
        content_type, body = handler_output.getContent()

    # Respond
    return {
        'statusCode': 200,
        "headers": {
            "Content-Type": f"{content_type}"
        },
        'body': body
    }

def main():

    scheme_help = 'Identifier for the threat model scheme (which contains location information)'
    doc_help = 'Location identifier of the document'
    template_help = 'Identifier for the document template (overrides template in scheme)'

    parser = argparse.ArgumentParser(description='Threatware is a tool to help review threat models and provide a process to manage threat models.  It works directly with threat models as Confluence/Google Docs documents.  For detailed help on deployment, configuration and customisation, see https://threatware.readthedocs.io')

    parser.add_argument("-l", "--lang", required=False, help="Language code for output texts")
    parser.add_argument("-f", "--format", required=False, help="Format for output, either JSON or YAML", default="json", choices=['json', 'yaml'])

    subparsers = parser.add_subparsers(dest="command")

    # convert
    parser_convert = subparsers.add_parser("convert", help='Convert a threat model for analysis')
    parser_convert.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_convert.add_argument('-d', '--docloc', required=True, help=doc_help)
    parser_convert.add_argument("-m", "--meta", required=False, help="What level of meta data about fields should be returned.  Note, 'properties' returns 'tags' as well.", default="tags", choices=['none', 'tags', 'properties'])

    # verify
    parser_convert = subparsers.add_parser("verify", help='Verify a threat model is ready to be submitted for approval')
    parser_convert.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_convert.add_argument('-d', '--docloc', required=True, help=doc_help)
    parser_convert.add_argument('-t', '--doctemplate', help=template_help)

    # manage
    parser_manage = subparsers.add_parser("manage", help='Manage the status of threat models')
    manage_subparsers = parser_manage.add_subparsers(dest="subcommand")
    # manage.indexdata
    parser_manage_indexdata = manage_subparsers.add_parser("indexdata", help='Get the threat model index metadata for a threat model')
    parser_manage_indexdata.add_argument('-id', required=True, help='The document ID for the threat model index metadata to return')
    # manage.createdata
    parser_manage_create = manage_subparsers.add_parser("create", help='Create a new document ID for a new threat model')
    parser_manage_create.add_argument('-idprefix', required=True, help='The prefix of the document ID e.g. "CMP.TMD"')
    parser_manage_create.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_manage_create.add_argument('-d', '--docloc', required=True, help=doc_help)
    # manage.check
    parser_manage_check = manage_subparsers.add_parser("check", help='Check whether the current threat model requires re-approval')
    parser_manage_check.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_manage_check.add_argument('-d', '--docloc', required=True, help=doc_help)
    # manage.submit
    parser_manage_submit = manage_subparsers.add_parser("submit", help='Submit a threat model for approval')
    parser_manage_submit.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_manage_submit.add_argument('-d', '--docloc', required=True, help=doc_help)
    
    # measure
    parser_measure = subparsers.add_parser("measure", help='Measure the distance of a TM from its template')
    parser_measure.add_argument('-s', '--scheme', required=True, help=scheme_help)
    parser_measure.add_argument('-d', '--docloc', required=True, help=doc_help)
    parser_measure.add_argument('-t', '--doctemplate', help=template_help)

    #parser.add_argument('-a', '--action', required=True, help='The action to perform', choices=[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE, ACTION_MEASURE])
    #parser.add_argument('-s', '--scheme', required=True, help='Identifier for the template scheme to load')
    #parser.add_argument('-d', '--docloc', required=True, help='Identifier for the document to verify')
    #parser.add_argument('-t', '--doctemplate', help='Identifier for the document template (overrides template in scheme)')
    #parser.add_argument('-v', '--verifiers', nargs='*', help='Space separated list of verifiers to use (overrides verifiers in mapping)')
    args = parser.parse_args()

    # Build input for handler
    event ={}

    class Object(object):
        pass
    context = Object()
    setattr(context, "threatware.cli", True)

    action = args.command
    if action == "manage":
        action = action + "." + args.subcommand

    event["queryStringParameters"] = {}
    event["queryStringParameters"]["lang"] = args.lang if "lang" in args else None
    event["queryStringParameters"]["format"] = args.format if "format" in args else None
    event["queryStringParameters"]["action"] = action
    event["queryStringParameters"]["scheme"] = args.scheme if "scheme" in args else None
    event["queryStringParameters"]["docloc"] = args.docloc if "docloc" in args else None
    event["queryStringParameters"]["meta"] = args.meta if "meta" in args else None
    event["queryStringParameters"]["doctemplate"] = args.doctemplate if "doctemplate" in args else None
    event["queryStringParameters"]["ID"] = args.id if "id" in args else None
    event["queryStringParameters"]["IDprefix"] = args.idprefix if "idprefix" in args else None
    #if args.verifiers:
    #    event["queryStringParameters"]["verifiers"] = ",".join(args.verifiers)

    response = lambda_handler(event, context)

    print(response["body"])

    return 


if __name__ == "__main__":
    sys.exit(main())