"""Script to orchestrate full pipeline: extract → transform → load to DynamoDB."""

import logging
import uuid
import boto3
import pandas as pd
from extract import extract_all_feeds
from transform import transform_data


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
    """Load transformed data into DynamoDB.

    Args:
        data: DataFrame from transform_data() pipeline
    """
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

    data_records = data.to_dict('records')

    for item in data_records:
        # Use existing columns or defaults for missing ones
        table.put_item(
            Item={
                'article_id': str(uuid.uuid4()),
                'published': str(item.get('published', 'N/A')),
                'title': str(item.get('title', 'N/A')),
                'author': str(item.get('author', 'N/A')),
                'link': str(item.get('link', 'N/A')),
                'tags': str(item.get('tags', 'N/A')),
                'content': str(item.get('content', 'N/A')),
                'individuals': str(item.get('individuals', 'N/A')),
                'companies': str(item.get('companies', 'N/A')),
                'sentiment': str(item.get('sentiment', 'N/A'))
            }
        )
        logging.debug(
            f"Loaded item into DynamoDB: {item.get('title', 'Unknown')}")

    logging.info("Finished loading data into DynamoDB.")
    return None


def run_full_pipeline(use_db=True, extract_only=False) -> pd.DataFrame:
    """Run the complete data pipeline: extract → transform → load.

    Args:
        use_db: Whether to load data to DynamoDB (default: True)
        extract_only: Only run extract, skip transform and load (default: False)

    Returns:
        pd.DataFrame: Transformed data that was loaded (or would be loaded)
    """
    logging.info("="*60)
    logging.info("PIPELINE START: Extract → Transform → Load")
    logging.info("="*60)

    # Step 1: Extract data from all feeds
    logging.info("\n[STEP 1/3] Extracting data from RSS feeds...")
    data = extract_all_feeds(save_local=False)
    logging.info(f"✓ Extracted {len(data)} articles")

    if extract_only:
        logging.info("\n[EXTRACT-ONLY MODE] Skipping transform and load")
        return data

    # Step 2: Transform data (clean, extract entities)
    logging.info("\n[STEP 2/3] Transforming data (clean, extract entities)...")
    data = transform_data(data)
    logging.info(f"✓ Transformed {len(data)} articles")

    # Step 3: Load to DynamoDB
    if use_db:
        logging.info("\n[STEP 3/3] Loading data to DynamoDB...")
        load_data(data)
        logging.info(f"✓ Loaded {len(data)} articles to DynamoDB")
    else:
        logging.info("\n[STEP 3/3] Skipping DynamoDB load (use_db=False)")

    logging.info("\n" + "="*60)
    logging.info("PIPELINE COMPLETE")
    logging.info("="*60)

    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Run the complete data pipeline')
    parser.add_argument('--no-db', action='store_true',
                        help='Skip loading to DynamoDB')
    parser.add_argument('--extract-only', action='store_true',
                        help='Only run extract step, skip transform and load')
    args = parser.parse_args()

    # Run the complete pipeline
    data = run_full_pipeline(
        use_db=not args.no_db,
        extract_only=args.extract_only
    )

    logging.info(f"\nFinal dataset shape: {data.shape}")
    logging.info(f"Columns: {list(data.columns)}")
