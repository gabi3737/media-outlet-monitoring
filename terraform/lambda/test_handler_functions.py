# pylint: skip-file
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import patch

from handler_functions import (
    get_individual,
    get_company,
    get_average_sentiment,
    get_time_period
)


@pytest.fixture
def valid_dataframe():
    """Valid pandas dataframe for testing"""
    return pd.DataFrame({
        "individuals": [
            ['test name', 'name', 'bob'],
            ['name test', 'test name'],
            ['xxx', 'yyy', 'zzz'],
            ['N/A'],
            []
        ],
        "companies": [
            ['test company', 'company', 'apple'],
            ['company test', 'test company'],
            ['banana', 'carrot', 'dinosaur'],
            ['N/A'],
            []
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


def test_get_individual_valid(valid_dataframe):
    filtered_data = get_individual(valid_dataframe, 'test name')
    assert len(filtered_data['individuals']) == 2
    assert filtered_data['individuals'][0] == ['test name', 'name', 'bob']
    assert filtered_data['individuals'][1] == ['name test', 'test name']


def test_get_individual_empty(valid_dataframe):
    filtered_data = get_individual(valid_dataframe, '')
    assert len(filtered_data['individuals']) == 0


def test_get_individual_none(valid_dataframe):
    filtered_data = get_individual(valid_dataframe, 'abc')
    assert len(filtered_data['individuals']) == 0


def test_get_company_valid(valid_dataframe):
    filtered_data = get_company(valid_dataframe, 'test company')
    assert len(filtered_data['companies']) == 2
    assert filtered_data['companies'][0] == [
        'test company', 'company', 'apple']
    assert filtered_data['companies'][1] == ['company test', 'test company']


def test_get_company_empty(valid_dataframe):
    filtered_data = get_company(valid_dataframe, '')
    assert len(filtered_data['companies']) == 0


def test_get_company_none(valid_dataframe):
    filtered_data = get_company(valid_dataframe, 'abc')
    assert len(filtered_data['companies']) == 0


def test_get_average_sentiment(valid_dataframe):
    assert get_average_sentiment(valid_dataframe) == {
        'average_sentiment': 0.5
    }


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
