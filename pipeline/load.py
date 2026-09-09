"""Script to load scraped data into DynamoDB."""

import logging
import uuid
import boto3
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def connect_to_db():
    """Connect to the DynamoDB table and return the table resource."""

    dynamodb = boto3.resource('dynamodb')
    logging.info("Connecting to DynamoDB.")
    table = dynamodb.Table('c25-gabi-db')

    return table


def get_most_recent_date(table) -> str:
    """Get the most recent published date from the DynamoDB table."""

    logging.debug("Fetching the most recent published date from DynamoDB.")

    dates = table.scan(
        ProjectionExpression="published"
    )

    published_dates = []

    for item in dates.get('Items', []):
        published_dates.append(pd.to_datetime(item['published']))

    if not published_dates:
        logging.debug("No published dates found in DynamoDB.")
        return None

    max_date = max(published_dates)
    return max_date


def load_data(data: pd.DataFrame) -> None:
    """Load scraped data into DynamoDB."""

    if data.empty:
        logging.warning("No data to load into DynamoDB.")
        return None

    table = connect_to_db()

    if table is None:
        logging.error("Failed to connect to DynamoDB.")
        return None

    most_recent_date = get_most_recent_date(table)
    logging.info(f"Most recent published date in DynamoDB: {most_recent_date}")

    if most_recent_date is not None:
        data = data[pd.to_datetime(data['published']) > most_recent_date]

        if data.empty:
            logging.info("DynamoDB contains all the most recent data.")
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
    return None
