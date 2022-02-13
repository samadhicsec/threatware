#!/usr/bin/env python3
"""
Makes available configuration for AWS Lambda execution context
"""

import logging
import json
import boto3
from botocore.exceptions import ClientError

import utils.logging
logger = logging.getLogger(utils.logging.getLoggerName(__name__))

class CLIContext:

    def __init__(self, config:dict):

        self.config = config
        self.secret_name = config.get("secret_name")
        self.region = config.get("region")

        self.secret_dict = json.loads(self._get_secret_get())

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
        
        confluence_conn = self.secret_dict.get("confluence")

        return confluence_conn



def load(config:dict):

    return CLIContext(config)