"""Script to load scraped data into DynamoDB."""

import logging
import uuid
import boto3
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def connect_to_db() -> boto3.resources.factory.dynamodb.Table:
    """Connect to the DynamoDB table and return the table resource."""

    dynamodb = boto3.resource('dynamodb')
    logging.info("Connecting to DynamoDB.")
    table = dynamodb.Table('c25-gabi-db')

    return table


def load_data(data: pd.DataFrame) -> None:
    """Load scraped data into DynamoDB."""

    table = connect_to_db()

    if table is None:
        logging.error("Failed to connect to DynamoDB.")
        return None

    if data.empty:
        logging.warning("No data to load into DynamoDB.")
        return None

    logging.info("Starting to load data into DynamoDB.")
    logging.info(f"Length of data to load into DynamoDB: {len(data)}")
    logging.debug(f"Data to load into DynamoDB: {data}")

    data = data.to_dict('records')

    for item in data:
        table.put_item(
            Item={
                'article_id': f"{uuid.uuid4()}",
                'published': f"{item['published']}",
                'title': f"{item['title']}",
                'author': f"{item['author']}",
                'link': f"{item['link']}",
                'tags': f"{item['tags']}",
                'content': f"{item['content']}",
                'individuals': f"{item['individuals']}",
                'companies': f"{item['companies']}",
                'sentiment': f"{item['sentiment']}"
            }
        )
        logging.debug(f"Loaded item into DynamoDB: {item['title']}")

    logging.info("Finished loading data into DynamoDB.")
