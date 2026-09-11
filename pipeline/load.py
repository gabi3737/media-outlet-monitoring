"""Script to orchestrate full pipeline: extract → transform → load to DynamoDB."""

import logging
import os
from decimal import Decimal
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
        # Convert sentiment to DynamoDB Number (Decimal). DynamoDB rejects NaN/Infinity.
        sentiment_value = item.get('sentiment', 0.0)
        try:
            sentiment_float = float(sentiment_value)
            if sentiment_float != sentiment_float or sentiment_float in (float('inf'), float('-inf')):
                raise ValueError("sentiment must be a finite number")
            sentiment_decimal = Decimal(f"{sentiment_float:.2f}")
        except (ValueError, TypeError):
            sentiment_decimal = Decimal('0.00')

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
                'sentiment': sentiment_decimal
            }
        )
        logging.debug(
            f"Loaded item into DynamoDB: {item.get('title', 'Unknown')}")

    logging.info("Finished loading data into DynamoDB.")
    return None


def save_data_locally(data: pd.DataFrame, format='csv') -> None:
    """Save transformed data to local CSV or JSON file.

    Args:
        data: DataFrame to save
        format: Output format ('csv' or 'json')
    """
    os.makedirs('data', exist_ok=True)

    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/transformed_feed_{timestamp}"

    if format == 'json':
        data.to_json(f"{filename}.json", orient='records', indent=2)
        logging.info(f"✓ Saved {len(data)} articles to {filename}.json")
    else:
        data.to_csv(f"{filename}.csv", index=False)
        logging.info(f"✓ Saved {len(data)} articles to {filename}.csv")


def run_full_pipeline(
        use_db=True,
        extract_only=False,
        save_local=False,
        local_format='csv') -> pd.DataFrame:
    """Run the complete data pipeline: extract → transform → load.

    Args:
        use_db: Whether to load data to DynamoDB (default: True)
        extract_only: Only run extract, skip transform and load (default: False)
        save_local: Save transformed data to local file instead of DB (default: False)
        local_format: Format for local save ('csv' or 'json', default: 'csv')

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

    # Step 3: Save/Load data
    if save_local:
        logging.info("\n[STEP 3/3] Saving data locally...")
        save_data_locally(data, format=local_format)
    elif use_db:
        logging.info("\n[STEP 3/3] Loading data to DynamoDB...")
        load_data(data)
        logging.info(f"✓ Loaded {len(data)} articles to DynamoDB")
    else:
        logging.info("\n[STEP 3/3] Skipping DynamoDB load (use_db=False)")

    logging.info("\n" + "="*60)
    logging.info("PIPELINE COMPLETE")
    logging.info("="*60)

    return data


def lambda_handler(event=None, context=None):
    """AWS Lambda handler for the ETL pipeline.

    Event parameters:
        - use_db (bool): Load to DynamoDB (default: True)
        - save_local (bool): Save to local file instead (default: False)
        - format (str): Output format 'csv' or 'json' (default: 'csv')
        - extract_only (bool): Only extract, skip transform/load (default: False)

    Returns:
        dict: Lambda response with statusCode and body
    """
    logging.info("Lambda handler invoked")

    try:
        # Parse event parameters
        use_db = event.get('use_db', True)
        save_local = event.get('save_local', False)
        local_format = event.get('format', 'csv')
        extract_only = event.get('extract_only', False)

        logging.info(
            f"Parameters: use_db={use_db}, save_local={save_local}, format={local_format}, extract_only={extract_only}")

        # Run pipeline
        data = run_full_pipeline(
            use_db=use_db,
            extract_only=extract_only,
            save_local=save_local,
            local_format=local_format
        )

        return {
            'statusCode': 200,
            'body': f"Successfully processed {len(data)} articles. Shape: {data.shape}"
        }
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': f"Pipeline error: {str(e)}"
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Run the complete data pipeline')
    parser.add_argument('--no-db', action='store_true',
                        help='Skip loading to DynamoDB')
    parser.add_argument('--extract-only', action='store_true',
                        help='Only run extract step, skip transform and load')
    parser.add_argument('--save-local', action='store_true',
                        help='Save transformed data to local file instead of DynamoDB')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Format for local save (default: csv)')
    args = parser.parse_args()

    # Run the complete pipeline
    data = run_full_pipeline(
        use_db=not args.no_db,
        extract_only=args.extract_only,
        save_local=args.save_local,
        local_format=args.format
    )

    logging.info(f"\nFinal dataset shape: {data.shape}")
    logging.info(f"Columns: {list(data.columns)}")
