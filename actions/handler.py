#!/usr/bin/env python3
"""
Handler to invoke verifier
"""

import logging
import sys
import argparse
import json
import utils.logging
from schemes.schemes import load_scheme
import actions.convert as convert
import actions.verify as verify

utils.logging.configureLogging()
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

ACTION_CONVERT = "convert"
ACTION_VERIFY = "verify"
ACTION_MANAGE = "manage"
ACTION_MEASURE = "measure"

def lambda_handler(event, context):

    # Get space and page from query string parameters
    qsp = event.get("queryStringParameters", {})
    action = qsp.get("action", None)
    schemeID = qsp.get("scheme", None)
    docloc = qsp.get("docloc", None)
    doctemplate = qsp.get("doctemplate", None)
    verifiers = qsp.get("verifiers", "").split(",")

    logger.info("Threat Model verifier: Scheme = '{}', Document Location = '{}', Document Template '{}', Verifiers = '{}'".format(schemeID, docloc, doctemplate, verifiers))

    # Validate input
    if action is None:
        error_str = "action is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif schemeID is None:
        error_str = "scheme is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif docloc is None:
        error_str = "docloc is a mandatory parameter"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})
    elif doctemplate is None and action == ACTION_VERIFY:
        error_str = f"doctemplate is a mandatory parameter when action = {ACTION_VERIFY}"
        logger.error(error_str)
        body = json.dumps({"message":"{}".format(error_str)})

    else:
        # If we are being called locally then we'll pull credentials locally
        if context.get("threatware.cli", False):
            # Get creds locally
            a = True
        else:
            # We are being called as a lambda, so get credentials from cloud
            a = True

        schemeDict = load_scheme(schemeID)

        if action == ACTION_CONVERT:
            # Convert the TM document
            
            doc_model = convert.convert(schemeDict, docloc)

            body = convert.tojson(doc_model)

        elif action == ACTION_VERIFY:

            # Convert the TM template
            template_model = convert.convert_template(schemeDict, doctemplate)

            # Convert the TM document
            doc_model = convert.convert(schemeDict, docloc)

            config = verify.config(schemeDict)

            # Verify the TM document
            issues =  verify.verify(config, doc_model, template_model)

            # Analyse coverage of threats
            coverage = verify.coverage(config, doc_model)

            # Generate a report on verification issues and analysis
            report = verify.report(config, issues, coverage)

            body = report.tojson()

        elif action == ACTION_MANAGE:
            # Convert the TM template
            doc_model = convert.convert(schemeDict, docloc)
            body = str(doc_model)
        elif action == ACTION_MEASURE:
            # Convert the TM template
            doc_model = convert.convert(schemeDict, docloc)
            body = str(doc_model)

    # Respond
    return {
        'statusCode': 200,
        'body': body
    }

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Threat Model Verifier')

    parser.add_argument('-a', '--action', required=True, help='The action to perform', choices=[ACTION_CONVERT, ACTION_VERIFY, ACTION_MANAGE, ACTION_MEASURE])
    parser.add_argument('-s', '--scheme', required=True, help='Identifier for the template scheme to load')
    parser.add_argument('-d', '--docloc', required=True, help='Identifier for the document to verify')
    parser.add_argument('-t', '--doctemplate', help='Identifier for the document template (overrides template in scheme)')
    #parser.add_argument('-v', '--verifiers', nargs='*', help='Space separated list of verifiers to use (overrides verifiers in mapping)')
    args = parser.parse_args()

    # Build input for handler
    event ={}
    context = {"threatware.cli":True}

    event["queryStringParameters"] = {}
    event["queryStringParameters"]["action"] = args.action
    event["queryStringParameters"]["scheme"] = args.scheme
    event["queryStringParameters"]["docloc"] = args.docloc
    event["queryStringParameters"]["doctemplate"] = args.doctemplate
    #if args.verifiers:
    #    event["queryStringParameters"]["verifiers"] = ",".join(args.verifiers)

    response = lambda_handler(event, context)

    sys.exit(print(response["body"]))