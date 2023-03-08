import boto3
import json
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

def get_secretsmanager_client(assume_role_arn):
    if assume_role_arn:
        sts_client = boto3.client('sts')

        assumed_role_object = sts_client.assume_role(
            RoleArn=assume_role_arn,
            RoleSessionName="valdate_connectors.py"
        )
        session = boto3.Session(
            aws_access_key_id=assumed_role_object['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role_object['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role_object['Credentials']['SessionToken']
        )
    else:
        session = boto3.Session()
    return session.client("secretsmanager")

def aws_secret(secretsmanager_client, secretsmanager_arn):
    try:
        response = secretsmanager_client.get_secret_value(**{
            'SecretId': secretsmanager_arn
        })
        result = [[]], json.loads(response["SecretString"])
    except secretsmanager_client.exceptions.ClientError as e:
        result = [["ERROR", secretsmanager_arn, e]], False
    except secretsmanager_client.exceptions.ResourceNotFoundException:
        result = [["ERROR", secretsmanager_arn, "not found"]], False
    except json.JSONDecodeError:
        result = [["ERROR", secretsmanager_arn, "invalid JSON"]], False

    return result

print(aws_secret(get_secretsmanager_client(None), sys.argv[1]))

