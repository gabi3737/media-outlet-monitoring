# pylint: skip-file
import logging
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from load import (
    connect_to_db,
    get_most_recent_date,
    load_data,
    run_full_pipeline,
)


@pytest.fixture
def sample_dataframe():
    """Sample transformed data for testing."""
    return pd.DataFrame({
        "published": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "title": ["Article 1", "Article 2", "Article 3"],
        "author": ["Author A", "Author B", "Author C"],
        "link": ["http://a.com", "http://b.com", "http://c.com"],
        "tags": ["tag1", "tag2", "tag3"],
        "content": ["Content 1", "Content 2", "Content 3"],
        "individuals": ["Person A", "Person B", "Person C"],
        "companies": ["Company A", "Company B", "Company C"],
        "sentiment": [0.75, 0.50, -0.25],
    })


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table resource."""
    table = MagicMock()
    table.scan.return_value = {
        "Items": [
            {"published": "2024-01-01T00:00:00"},
            {"published": "2024-01-02T00:00:00"},
        ]
    }
    return table


@patch("load.boto3.resource")
def test_connect_to_db(mock_boto3_resource):
    """Test that connect_to_db returns the correct table."""
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    table = connect_to_db()

    mock_boto3_resource.assert_called_once_with("dynamodb")
    mock_boto3_resource.return_value.Table.assert_called_once_with(
        "c25-gabi-db")
    assert table == mock_table


def test_get_most_recent_date_with_data(mock_dynamodb_table):
    """Test fetching most recent date when data exists."""
    result = get_most_recent_date(mock_dynamodb_table)
    expected = pd.to_datetime("2024-01-02T00:00:00")
    assert result == expected


def test_get_most_recent_date_no_data():
    """Test when DynamoDB has no items."""
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": []}

    result = get_most_recent_date(mock_table)
    assert result is None


@patch("load.connect_to_db")
@patch("load.uuid.uuid4")
def test_load_data_happy_path(mock_uuid, mock_connect, sample_dataframe, mock_dynamodb_table):
    """Test loading data when DynamoDB is empty (all rows should be inserted)."""
    mock_connect.return_value = mock_dynamodb_table
    mock_dynamodb_table.scan.return_value = {"Items": []}
    mock_uuid.side_effect = [
        "id-1",
        "id-2",
        "id-3",
    ]

    load_data(sample_dataframe)

    assert mock_dynamodb_table.put_item.call_count == 3


@patch("load.connect_to_db")
def test_load_data_no_new_records(mock_connect, sample_dataframe, mock_dynamodb_table, caplog):
    """Test when all records already exist in DynamoDB (no new inserts)."""
    mock_connect.return_value = mock_dynamodb_table
    mock_dynamodb_table.scan.return_value = {
        "Items": [{"published": "2024-01-03T00:00:00"}]
    }

    with caplog.at_level(logging.INFO):
        load_data(sample_dataframe)

    mock_dynamodb_table.put_item.assert_not_called()
    assert "DynamoDB contains all the most recent data" in caplog.text


@patch("load.connect_to_db")
def test_load_data_empty_dataframe(mock_connect, caplog):
    """Test load_data with empty DataFrame."""
    mock_table = MagicMock()
    mock_connect.return_value = mock_table
    empty_df = pd.DataFrame()

    with caplog.at_level(logging.WARNING):
        load_data(empty_df)

    mock_table.put_item.assert_not_called()
    assert "No data to load into DynamoDB" in caplog.text


def test_load_data_invalid_sentiment(mock_dynamodb_table):
    """Test that invalid sentiment values are handled correctly."""
    data = pd.DataFrame({
        "published": ["2024-01-01"],
        "title": ["Test"],
        "author": ["Author"],
        "link": ["http://test.com"],
        "tags": ["tag"],
        "content": ["content"],
        "individuals": ["person"],
        "companies": ["company"],
        "sentiment": [float("nan")],
    })

    with patch("load.connect_to_db", return_value=mock_dynamodb_table):
        with patch("load.uuid.uuid4", return_value="test-id"):
            mock_dynamodb_table.scan.return_value = {"Items": []}
            load_data(data)

    call_args = mock_dynamodb_table.put_item.call_args
    sentiment_value = call_args[1]["Item"]["sentiment"]
    assert sentiment_value == Decimal("0.00")


@patch("load.extract_all_feeds")
@patch("load.transform_data")
def test_run_full_pipeline_no_db(mock_transform, mock_extract, sample_dataframe, caplog):
    """Test pipeline with use_db=False."""
    mock_extract.return_value = sample_dataframe
    mock_transform.return_value = sample_dataframe

    with caplog.at_level(logging.INFO):
        result = run_full_pipeline(use_db=False)

    assert "Skipping DynamoDB load" in caplog.text
    assert len(result) == len(sample_dataframe)
