#!/usr/bin/env python3
"""
Handler to invoke verifier
"""

import logging
import sys
import argparse
import json
import utils.logging
from providers import provider
from language.translate import Translate
from schemes.schemes import load_scheme
import actions.convert as convert
import actions.verify as verify
import actions.manage as manage

utils.logging.configureLogging()
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

ACTION_CONVERT = "convert"
ACTION_VERIFY = "verify"
ACTION_MANAGE_INDEXDATA = "manage.indexdata"
ACTION_MANAGE_CREATE = "manage.create"
ACTION_MANAGE_SUBMIT = "manage.submit"
ACTION_MANAGE_CHECK = "manage.check"
ACTION_MEASURE = "measure"

def lambda_handler(event, context):

    # Get space and page from query string parameters
    qsp = event.get("queryStringParameters", {})
    action = qsp.get("action", None)
    schemeID = qsp.get("scheme", None)
    docloc = qsp.get("docloc", None)
    doctemplate = qsp.get("doctemplate", None)
    id = qsp.get("ID", None)
    IDprefix = qsp.get("IPprefix", None)
    #verifiers = qsp.get("verifiers", "").split(",")

    logger.info(f"Threatware called with parameters = '{qsp}'")

    # Validate input
    if action is None:
        error_str = "action is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif action in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and schemeID is None:
        error_str = "scheme is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif action in [ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE_CREATE, ACTION_MANAGE_SUBMIT, ACTION_MANAGE_CHECK, ACTION_MEASURE] and docloc is None:
        error_str = "docloc is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif action in [ACTION_VERIFY] and  doctemplate is None:
        error_str = f"doctemplate is a mandatory parameter when action = {action}"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif action in [ACTION_MANAGE_INDEXDATA] and id is None:
        error_str = f"ID is a mandatory parameter when action = {action}"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif action in [ACTION_MANAGE_CREATE] and IDprefix is None:
        error_str = f"IDprefix is a mandatory parameter when action = {action}"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})

    else:
        # If we are being called locally then we'll pull credentials locally
        if context.get("threatware.cli", False):
            # Get creds locally
            execution_env = provider.get_provider("cli")
        else:
            # We are being called as a lambda, so get credentials from cloud
            execution_env = provider.get_provider("aws.lambda")

        # We need this to support localisation of keywords
        translator = Translate()

        if schemeID is not None:
            schemeDict = load_scheme(schemeID)

        if action == ACTION_CONVERT:
            # Convert the TM document
            
            doc_model = convert.convert(execution_env, schemeDict, docloc)

            body = convert.tojson(doc_model)

        elif action == ACTION_VERIFY:

            # Convert the TM template
            template_model = convert.convert_template(execution_env, schemeDict, doctemplate)

            # Convert the TM document
            doc_model = convert.convert(execution_env, schemeDict, docloc)

            config = verify.config(schemeDict)

            # Verify the TM document
            issues =  verify.verify(config, doc_model, template_model)

            # Analyse coverage of threats
            coverage = verify.coverage(config, doc_model)

            # Generate a report on verification issues and analysis
            report = verify.report(config, issues, coverage)

            body = report.tojson()

        elif action == ACTION_MANAGE_INDEXDATA:
            
            config = manage.config(translator)

            output = manage.output(config)

            result = manage.indexdata(config, output, id)

            body = output.tojson(result)

        elif action == ACTION_MANAGE_SUBMIT:
            
            config = manage.config(translator)

            output = manage.output(config)

            # Convert the TM template
            doc_model = convert.convert(execution_env, schemeDict, docloc)

            result = manage.submit(config, output, docloc, schemeID, doc_model)

            body = output.tojson(result)

        elif action == ACTION_MEASURE:
            # Convert the TM template
            doc_model = convert.convert(execution_env, schemeDict, docloc)
            body = str(doc_model)

    # Respond
    return {
        'statusCode': 200,
        'body': body
    }

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Threat Model Verifier')

    subparsers = parser.add_subparsers(dest="command")

    #convert
    parser_convert = subparsers.add_parser("convert", help='Convert a threat model for analysis')
    parser_convert.add_argument('-s', '--scheme', required=True, help='Identifier for the threat model scheme (which contains location information)')
    parser_convert.add_argument('-d', '--docloc', required=True, help='Location identifier of the document')

    # verify
    parser_convert = subparsers.add_parser("verify", help='Verify a threat model is ready to be submitted for approval')
    parser_convert.add_argument('-s', '--scheme', required=True, help='Identifier for the threat model scheme (which contains location information)')
    parser_convert.add_argument('-d', '--docloc', required=True, help='Location identifier of the document')
    parser_convert.add_argument('-t', '--doctemplate', help='Identifier for the document template (overrides template in scheme)')

    # manage
    parser_manage = subparsers.add_parser("manage", help='Manage the status of threat models')
    manage_subparsers = parser_manage.add_subparsers(dest="subcommand")
    # manage.indexdata
    parser_manage_indexdata = manage_subparsers.add_parser("indexdata", help='Get the threat model index metadata for a threat model')
    parser_manage_indexdata.add_argument('-id', required=True, help='The document ID for the threat model index metadata to return')
    # manage.createdata
    parser_manage_create = manage_subparsers.add_parser("create", help='Create a new document ID for a new threat model')
    parser_manage_create.add_argument('-idprefix', required=True, help='The prefix of the document ID e.g. "CMP.TMD"')
    parser_manage_create.add_argument('-s', '--scheme', required=True, help='Identifier for the threat model scheme (which contains location information)')
    parser_manage_create.add_argument('-d', '--docloc', required=True, help='Location identifier of the document')
    # manage.check
    parser_manage_check = manage_subparsers.add_parser("check", help='Check whether the current threat model requires re-approval')
    parser_manage_check.add_argument('-s', '--scheme', required=True, help='Identifier for the threat model scheme (which contains location information)')
    parser_manage_check.add_argument('-d', '--docloc', required=True, help='Location identifier of the document')
    # manage.submit
    parser_manage_submit = manage_subparsers.add_parser("submit", help='Submit a threat model for approval')
    parser_manage_submit.add_argument('-s', '--scheme', required=True, help='Identifier for the threat model scheme (which contains location information)')
    parser_manage_submit.add_argument('-d', '--docloc', required=True, help='Location identifier of the document')
    

    #parser.add_argument('-a', '--action', required=True, help='The action to perform', choices=[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE, ACTION_MEASURE])
    #parser.add_argument('-s', '--scheme', required=True, help='Identifier for the template scheme to load')
    #parser.add_argument('-d', '--docloc', required=True, help='Identifier for the document to verify')
    #parser.add_argument('-t', '--doctemplate', help='Identifier for the document template (overrides template in scheme)')
    #parser.add_argument('-v', '--verifiers', nargs='*', help='Space separated list of verifiers to use (overrides verifiers in mapping)')
    args = parser.parse_args()

    # Build input for handler
    event ={}
    context = {"threatware.cli":True}

    action = args.command
    if action == "manage":
        action = action + "." + args.subcommand

    event["queryStringParameters"] = {}
    event["queryStringParameters"]["action"] = action
    event["queryStringParameters"]["scheme"] = args.scheme if "scheme" in args else None
    event["queryStringParameters"]["docloc"] = args.docloc if "docloc" in args else None
    event["queryStringParameters"]["doctemplate"] = args.doctemplate if "doctemplate" in args else None
    event["queryStringParameters"]["ID"] = args.id if "id" in args else None
    event["queryStringParameters"]["IDprefix"] = args.idprefix if "idprefix" in args else None
    #if args.verifiers:
    #    event["queryStringParameters"]["verifiers"] = ",".join(args.verifiers)

    response = lambda_handler(event, context)

    sys.exit(print(response["body"]))