# pylint: skip-file
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import patch

from handler_functions import (
    get_clean_data,
    get_individual,
    get_company_from_db,
    get_average_sentiment,
    get_time_period
)


@pytest.fixture
def valid_dataframe():
    """Valid pandas dataframe for testing"""
    return pd.DataFrame({
        "tags": [
            "['a', 'b']",
            "['c', 'd']",
            "['N/A]",
            "[]",
            "['nothing']"
        ],
        "author": [
            "['a', 'b']",
            "['c', 'd']",
            "['N/A]",
            "[]",
            "['nothing']"
        ],
        "individuals": [
            "[test name, name, bob]",
            "[name test, test name]",
            "[xxx, yyy, zzz]",
            "[N/A]",
            "[]"
        ],
        "companies": [
            "[test company, company, apple]",
            "[company test, test company]",
            "[banana, carrot, dinosaur]",
            "[N/A]",
            "[]"
        ],
        "sentiment": [
            0.0,
            1.0,
            0.5,
            0.5,
            0.5
        ],
        "published": [
            datetime(2026, 6, 12, 0, 0, 0, 0),
            datetime(2026, 6, 13, 0, 0, 0, 0),
            datetime(2026, 6, 14, 0, 0, 0, 0),
            datetime(2026, 2, 10, 0, 0, 0, 0),
            datetime(2026, 2, 15, 0, 0, 0, 0)
        ]
    })


@pytest.fixture
def empty_dataset():
    """Empty dataset"""
    return pd.DataFrame({
        'tags': [],
        'author': [],
        'individuals': [],
        'companies': [],
        'sentiment': [],
        'published': []
    })


def test_get_clean_data_valid(valid_dataframe):
    clean_data = get_clean_data(valid_dataframe)
    assert len(clean_data) == 5
    assert isinstance(clean_data, pd.DataFrame)
    assert clean_data.iloc[0].to_dict() == {
        'tags': ['a', 'b'],
        'author': ['a', 'b'],
        'individuals': ['test name', 'name', 'bob'],
        'companies': ['test company', 'company', 'apple'],
        'sentiment': 0.0,
        'published': datetime(2026, 6, 12, 0, 0, 0, 0),
        'date': datetime(2026, 6, 12, 0, 0, 0, 0).date()
    }


def test_get_clean_data_empty(empty_dataset):
    clean_data = get_clean_data(empty_dataset)
    pd.testing.assert_frame_equal(clean_data, empty_dataset)


def test_get_individual_valid(valid_dataframe):
    filtered_data = get_individual(valid_dataframe, 'test name')
    assert len(filtered_data) == 2
    assert filtered_data[0]['individuals'] == ['test name', 'name', 'bob']
    assert filtered_data[1]['individuals'] == ['name test', 'test name']


def test_get_individual_empty(empty_dataset):
    filtered_data = get_individual(empty_dataset, '')
    assert len(filtered_data) == 0


def test_get_individual_none(valid_dataframe):
    filtered_data = get_individual(valid_dataframe, 'abc')
    assert len(filtered_data) == 0


def test_get_company_valid(valid_dataframe):
    filtered_data = get_company_from_db(valid_dataframe, 'test company')
    assert len(filtered_data) == 2
    assert filtered_data[0]['companies'] == [
        'test company', 'company', 'apple']
    assert filtered_data[1]['companies'] == ['company test', 'test company']


def test_get_company_empty(empty_dataset):
    filtered_data = get_company_from_db(empty_dataset, '')
    assert len(filtered_data) == 0


def test_get_company_none(valid_dataframe):
    filtered_data = get_company_from_db(valid_dataframe, 'abc')
    assert len(filtered_data) == 0


def test_get_average_sentiment(valid_dataframe):
    assert get_average_sentiment(valid_dataframe) == {
        'average_sentiment': 0.5
    }


def test_get_average_sentiment_empty(empty_dataset):
    assert get_average_sentiment(empty_dataset) == {'error': 'Empty dataset'}


@patch("handler_functions.date")
def test_get_time_period_valid(mock_date, valid_dataframe):
    mock_date.today.return_value = date(2026, 6, 20)
    valid_dataframe['published'] = pd.to_datetime(
        valid_dataframe['published'], errors='coerce')
    filtered_data = get_time_period(valid_dataframe, 20)
    assert len(filtered_data['published']) == 3
    assert filtered_data['published'][0] == datetime(2026, 6, 12, 0, 0, 0, 0)
    assert filtered_data['published'][1] == datetime(2026, 6, 13, 0, 0, 0, 0)
    assert filtered_data['published'][2] == datetime(2026, 6, 14, 0, 0, 0, 0)
