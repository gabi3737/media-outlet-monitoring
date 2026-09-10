import json
import os
import logging
from dotenv import load_dotenv
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import pandas as pd

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# Apparently needed for handling Decimal types in JSON or the whole thing crashes, as
# DynamoDB uses `Decimal` instead of `float` for numeric values and JSON does not like that.


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def handler(event, context):
    data = load_data()
    logger.info("Received event: %s", json.dumps(event))
    route = event['routeKey']
    try:

        if route == "GET /keywords/{keyword}":
            return get_keywords(event, data)
        elif route == "GET /articles/{id}":
            return get_article(event, data)
        else:
            return {
                "statusCode": 404,
                "body": "Route not found"
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": str(e)
        }


def load_data() -> pd.DataFrame:
    """Load data from the DynamoDB"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('c25-gabi-db')

    response = table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    return pd.DataFrame(items)


def get_keywords(event, data):

    return respond(200, data)


def get_article(event, data):

    return respond(200, data)


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=decimal_default)
    }
