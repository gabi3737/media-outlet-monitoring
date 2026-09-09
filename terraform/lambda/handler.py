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
    route = event['routeKey']
    try:

        if route == "GET /keywords/{keyword}":
            return get_keywords(event)
        elif route == "GET /articles/{id}":
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


def get_keywords(event):
    keyword = event['pathParameters']['keyword']
    response = table.query(
        IndexName="keyword-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key(
            "keyword").eq(keyword)
    )
    items = response.get("Items", [])
    if not items:
        return respond(404, {"error": "Keyword not found."})
    return respond(200, {"items": items,
                         'total': len(items)})


def get_article(event):
    article_id = event['pathParameters']['id']
    response = table.get_item(Key={"id": article_id})
    item = response.get("Item")
    if not item:
        return respond(404, {"error": "Article not found."})
    return respond(200, item)


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default=decimal_default)
    }
