"""Script to load scraped data into DynamoDB."""

import logging
import uuid
import boto3


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_data(data: dict) -> None:
    """Load scraped data into DynamoDB."""

    if not data:
        logging.warning("No data to load into DynamoDB.")
        return

    dynamodb = boto3.resource('dynamodb')
    logging.info("Connecting to DynamoDB.")
    table = dynamodb.Table('c25-gabi-db')

    try:
        table.load()
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        logging.error("DynamoDB table 'c25-gabi-db' not found.")
        return

    logging.info("Starting to load data into DynamoDB.")
    logging.info(f"Length of data to load into DynamoDB: {len(data)}")
    logging.debug(f"Data to load into DynamoDB: {data}")

    data = data.to_dict('records')

    for item in data:
        table.put_item(
            Item={
                'PrimaryKey': f"{uuid.uuid4()}",
                'SortKey': f"{item['publication_time']}",
                'Outlet': f"{item['outlet']}",
                'Title': f"{item['title']}",
                'Content': f"{item['content']}",
                'Author': f"{item['author']}",
                'Keywords': f"{item['keywords']}",
                'Individuals': f"{item['individuals']}",
                'Companies': f"{item['companies']}",
                'Sentiment': f"{item['sentiment']}"
            }
        )
        logging.debug(f"Loaded item into DynamoDB: {item['title']}")

    logging.info("Finished loading data into DynamoDB.")
