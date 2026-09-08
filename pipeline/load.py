"""Script to load scraped data into DynamoDB."""

import logging
import uuid
import boto3


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def connect_to_db() -> boto3.resources.factory.dynamodb.Table:
    """Connect to the DynamoDB table and return the table resource."""

    dynamodb = boto3.resource('dynamodb')
    logging.info("Connecting to DynamoDB.")
    table = dynamodb.Table('c25-gabi-db')

    try:
        table.load()
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        logging.error("DynamoDB table 'c25-gabi-db' not found.")
        return None

    return table


def load_data(data: dict) -> None:
    """Load scraped data into DynamoDB."""

    table = connect_to_db()

    if table is None:
        logging.error("Failed to connect to DynamoDB.")
        return None

    if not data:
        logging.warning("No data to load into DynamoDB.")
        return None

    logging.info("Starting to load data into DynamoDB.")
    logging.info(f"Length of data to load into DynamoDB: {len(data)}")
    logging.debug(f"Data to load into DynamoDB: {data}")

    data = data.to_dict('records')

    for item in data:
        table.put_item(
            Item={
                'PrimaryKey': f"{uuid.uuid4()}",
                'SortKey': f"{item['published']}",
                'Title': f"{item['title']}",
                'Author': f"{item['author']}",
                'Link': f"{item['link']}",
                'Tags': f"{item['tags']}",
                'Content': f"{item['content']}",
                'Individuals': f"{item['individuals']}",
                'Companies': f"{item['companies']}",
                'Sentiment': f"{item['sentiment']}"
            }
        )
        logging.debug(f"Loaded item into DynamoDB: {item['title']}")

    logging.info("Finished loading data into DynamoDB.")
