"""
Test for the transform.py file
"""
import pytest
import pandas as pd

from transform import (
    clean_publication_time,
    clean_string_columns,
    clean_author_column
)


@pytest.fixture
def valid_dataframe():
    """Valid pandas dataframe for testing"""
    return pd.DataFrame({
        "published": [
            "Mon, 07 Sep 2026 10:30:00 +0000",
            "Thu, 27 Aug 2026 14:01:00 GMT",
        ],
        "title": [
            " test TITLE onE ",
            "  TEST title tWo",
        ],
        "content": [
            " test one  ",
            " test  two   ",
        ],
        "author": [
            " Lily Hay Newman, Matt Burgess, Dhruv Mehrotra   ",
            " mmarshall@venturebeat.com (Matt Marshall)",
        ],
        "tags": [
            "Gear, Gear / Gear News and Events, artificial intelligence, Say More",
            " Machine Learning / AI ",
        ]
    })


@pytest.fixture
def empty_dataframe():
    """Pandas dataframe with null values for testing"""
    return pd.DataFrame({
        "published": [None],
        "title": [None],
        "content": [None],
        "author": [None],
        "tags": [None]
    })


@pytest.fixture
def invalid_dataframe():
    """Invalid pandas dataframe values for testing"""
    return pd.DataFrame({
        "published": ["Hello"],
        "title": [123],
        "content": [123],
        "author": [123],
        "tags": [123]
    })


def test_clean_publication_time_valid(valid_dataframe):
    """Tests the clean_publication_time function with valid data"""
    result = clean_publication_time(valid_dataframe)

    assert result["published"].iloc[0] == pd.Timestamp(
        "2026-09-07 10:30:00+00:00"
    )
    assert result["published"].iloc[1] == pd.Timestamp(
        "2026-08-27 14:01:00+00:00"
    )


def test_clean_publication_time_empty(empty_dataframe):
    """Tests the clean_publication_time function with null values"""
    result = clean_publication_time(empty_dataframe)
    assert pd.isna(result["published"].iloc[0])


def test_clean_publication_time_invalid(invalid_dataframe):
    """Tests the clean_publication_time function with invalid data"""
    result = clean_publication_time(invalid_dataframe)
    assert pd.isna(result["published"].iloc[0])


def test_clean_string_columns_valid(valid_dataframe):
    """Tests the clean_string_columns function with valid data"""
    result = clean_string_columns(valid_dataframe)
    assert result["title"].iloc[0] == "test TITLE onE"
    assert result["title"].iloc[1] == "TEST title tWo"

    assert result["content"].iloc[0] == "test one"
    assert result["content"].iloc[1] == "test  two"

    assert set(result["tags"].iloc[0]) == {'gear',
                                           'gear news and events',
                                           'artificial intelligence',
                                           'say more'}
    assert set(result["tags"].iloc[1]) == {'machine learning', 'ai'}


def test_clean_string_columns_empty(empty_dataframe):
    """Tests the clean_string_columns function with null values"""
    result = clean_string_columns(empty_dataframe)
    assert pd.isna(result["title"].iloc[0])
    assert pd.isna(result["content"].iloc[0])
    assert result["tags"].iloc[0] == []


def test_clean_string_columns_invalid(invalid_dataframe):
    """Tests the clean_string_columns function with invalid data"""
    result = clean_string_columns(invalid_dataframe)
    assert result["title"].iloc[0] == "123"
    assert result["content"].iloc[0] == "123"
    assert result["tags"].iloc[0] == ['123']


def test_clean_author_column_valid(valid_dataframe):
    """Tests the clean_author_column with valid data"""
    result = clean_author_column(valid_dataframe)
    assert result["author"].iloc[0] == [
        "Lily Hay Newman", "Matt Burgess", "Dhruv Mehrotra"]
    assert result["author"].iloc[1] == ["Matt Marshall"]


def test_clean_author_column_empty(empty_dataframe):
    """Tests the clean_author_column with null values"""
    result = clean_author_column(empty_dataframe)
    assert result["author"].iloc[0] is None


def test_clean_author_column_invalid(invalid_dataframe):
    """Tests the clean_author_column with invalid data"""
    result = clean_author_column(invalid_dataframe)
    assert result["author"].iloc[0] == ["123"]
