import json
from os import environ
from dotenv import load_dotenv
import logging
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

load_dotenv()
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(environ['TABLE_NAME'])


def get_keywords(word: str):
    response = table.scan(
        FilterExpression=Key("tags").eq(
            word),
        Limit=10,
    )
    items = []
    for item in response['Items']:
        items.append(item['tags'])
    return print(items)


get_keywords("")
