import time
import pandas as pd
import json
import os
import logging
from dotenv import load_dotenv
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

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

        if route == "GET /person/{person}":
            return get_person(event, data)
        elif route == "GET /company/{company}":
            return get_company(event, data)
        elif route == "GET /person/{person}/sentiment":
            return get_person_sentiment(event, data)
        elif route == "GET /company/{company}/sentiment":
            return get_company_sentiment(event, data)
        elif route == "GET /articles":
            return get_articles(event, data)

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


_data_cache = None
_cache_timestamp = None
CACHE_TTL_SECONDS = 3600


def load_data() -> pd.DataFrame:
    """Load data from DynamoDB with caching."""
    global _data_cache, _cache_timestamp

    now = time.time()
    if _data_cache is not None and _cache_timestamp is not None:
        if now - _cache_timestamp < CACHE_TTL_SECONDS:
            logger.info("Using cached data (age: %.0fs).",
                        now - _cache_timestamp)
            return _data_cache

    logger.info("Refreshing data from DynamoDB.")
    response = table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    _data_cache = pd.DataFrame(items)
    _cache_timestamp = now
    return _data_cache


def get_person(event, data):
    person = event['pathParameters']['person']

    return respond(200, data)


def get_company(event, data):
    company = event['pathParameters']['company']

    return respond(200, data)


def get_person_sentiment(event, data):
    person = event['pathParameters']['person']

    return respond(200, data)


def get_company_sentiment(event, data):
    company = event['pathParameters']['company']

    return respond(200, data)


def get_articles(event, data):
    return respond(200, data)


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=decimal_default)
    }
