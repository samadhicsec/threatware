#!/usr/bin/env python3
"""
Makes available configuration for AWS Lambda execution context
"""

import logging
import os
import json
import boto3
from botocore.exceptions import ClientError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class AWSLambdaContext:

    def __init__(self, config:dict):
        # Needs to be able to handle an empty config because providers may get called before config files are available.

        self.config = config
        if "secret_name" in config:
            self.secret_name = config.get("secret_name")
        else:
            # Read from env var if possible
            self.secret_name = os.getenv("THREATWARE_AWS_SECRET_NAME")

        if "region" in config: 
            self.region = config.get("region")
        else:
            # Read from env var if possible
            self.region = os.getenv("THREATWARE_AWS_SECRET_REGION")

        self.secret_dict = {}
        if self.secret_name is not None and self.region is not None:
            self.secret_dict = json.loads(self._get_secret())

    def _get_secret(self):

        # This code taken from https://boto3.amazonaws.com/v1/documentation/api/latest/guide/secrets-manager.html

        secret_name = self.secret_name
        region_name = self.region

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"The requested secret '{secret_name}' was not found")
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                logger.error(f"The request was invalid due to: {e}")
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                logger.error(f"The request had invalid params: {e}")
            elif e.response['Error']['Code'] == 'DecryptionFailure':
                logger.error(f"The requested secret can't be decrypted using the provided KMS key: {e}")
            elif e.response['Error']['Code'] == 'InternalServiceError':
                logger.error(f"An error occurred on service side: {e}")
        else:
            # Secrets Manager decrypts the secret value using the associated KMS CMK
            # Depending on whether the secret was a string or binary, only one of these fields will be populated
            if 'SecretString' in get_secret_value_response:
                text_secret_data = get_secret_value_response['SecretString']
            else:
                logger.error(f"No 'SecretString' was available in secret '{secret_name}'")
                #binary_secret_data = get_secret_value_response['SecretBinary']

        return text_secret_data

    def getConfluenceConnectionCredentials(self):
        
        confluence_conn = json.loads(self.secret_dict.get("confluence"))

        return confluence_conn

    def getGoogleCredentials(self):

        credentials = json.loads(self.secret_dict.get("google"))

        return credentials

    def getGitCredentials(self):

        credentials = json.loads(self.secret_dict.get("git"))

        return credentials

    def get_config_base_dir(self, suggested_base_dir):
        """ Return the directory where we expect the configuration file to be based 
        
        Returns
        -------
        str : The suggested base directory to find configuration file
        bool : Whether this environment is ephemeral (config will not persist between invocations)
        """

        # We can only write to /tmp for lambdas, so need to check suggestion does that, and if not move it there
        real_suggested_base_dir = os.path.realpath(os.path.normpath(suggested_base_dir))

        # Compare dir /tmp to the shared path between /tmp and the suggestion (which will be /tmp if the suggested path starts with /tmp)
        if os.path.samefile("/tmp", os.path.commonpath(["/tmp", real_suggested_base_dir])):
            base_dir = real_suggested_base_dir
        else:
            if os.path.isabs(real_suggested_base_dir):
                head, tail = os.path.split(real_suggested_base_dir)
                base_dir = os.path.join("/tmp", tail)
            else:
                base_dir = os.path.join("/tmp", real_suggested_base_dir)

        # The config will NOT persist after execution
        return base_dir, True

def load(config:dict):

    return AWSLambdaContext(config)