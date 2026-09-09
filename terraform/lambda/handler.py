import json
import os
import logging
import boto3
from decimal import Decimal

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
    logger.info("Received event: %s", json.dumps(event))
    route = event.get("routeKey", "")
    try:

        if route == "GET /analysis":
            return get_analysis(event)
        elif route == "GET /items/{id}":
            return get_article(event)
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


def get_analysis(event):
    pass


def get_article(event):
    pass


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=decimal_default)
    }
