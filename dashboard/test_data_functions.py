# pylint: skip-file


import pytest
import pandas as pd

from data_functions import (get_clean_data,
                            get_average_sentiment,
                            get_company_mention_count,
                            get_average_sentiment_by_company,
                            get_average_sentiment_for_top_companies,
                            get_daily_sentiment)


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'published': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'companies': ['[Company A]', 'Company B', 'Company A'],
        'tags': ['[Tag1]', 'Tag2', 'Tag1'],
        'individuals': ['[Person1]', 'Person2', 'Person1'],
        'author': ['[Author1]', 'Author2', 'Author1'],
        'sentiment': [0.5, 0.3, 0.7]
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


def test_get_clean_data_columns(sample_data):
    cleaned_data = get_clean_data(sample_data)
    expected_columns = ['published', 'companies',
                        'tags', 'individuals', 'author', 'sentiment']
    assert all(column in cleaned_data.columns for column in expected_columns)


def test_get_clean_data_correct_companies(sample_data):
    cleaned_data = get_clean_data(sample_data)
    assert cleaned_data['companies'].iloc[0] == ['Company A']
    assert cleaned_data['companies'].iloc[1] == ['Company B']


def test_get_clean_data_correct_tags(sample_data):
    cleaned_data = get_clean_data(sample_data)
    assert cleaned_data['tags'].iloc[0] == ['Tag1']
    assert cleaned_data['tags'].iloc[1] == ['Tag2']


def test_get_clean_data_correct_individuals(sample_data):
    cleaned_data = get_clean_data(sample_data)
    assert cleaned_data['individuals'].iloc[0] == ['Person1']
    assert cleaned_data['individuals'].iloc[1] == ['Person2']


def test_get_clean_data_correct_author(sample_data):
    cleaned_data = get_clean_data(sample_data)
    assert cleaned_data['author'].iloc[0] == ['Author1']
    assert cleaned_data['author'].iloc[1] == ['Author2']


def test_get_clean_data_empty(empty_dataset):
    clean_data = get_clean_data(empty_dataset)
    pd.testing.assert_frame_equal(clean_data, empty_dataset)


def test_get_average_sentiment(sample_data):
    average_sentiment = get_average_sentiment(sample_data)
    expected_average = (
        sample_data['sentiment'].iloc[0] + sample_data['sentiment'].iloc[1] + sample_data['sentiment'].iloc[2]) / 3
    assert average_sentiment == expected_average


def test_get_company_mention_count(sample_data):
    company_count = get_company_mention_count(sample_data)
    assert company_count == 3


def test_get_average_sentiment_by_company(sample_data):
    cleaned_data = get_clean_data(sample_data)
    average_sentiment_by_company = get_average_sentiment_by_company(
        cleaned_data)
    expected_average = pd.DataFrame({
        'companies': ['Company A', 'Company B'],
        'sentiment': [(sample_data['sentiment'].iloc[0] + sample_data['sentiment'].iloc[2]) / 2, sample_data['sentiment'].iloc[1]]
    })
    pd.testing.assert_frame_equal(
        average_sentiment_by_company.reset_index(drop=True),
        expected_average.reset_index(drop=True)
    )


def test_get_average_sentiment_for_top_companies(sample_data):
    cleaned_data = get_clean_data(sample_data)
    top_companies_sentiment = get_average_sentiment_for_top_companies(
        cleaned_data)
    top_companies_sentiment = top_companies_sentiment.head(1)
    expected_top_company_sentiment = pd.DataFrame({
        'companies': ['Company A'],
        'count': [2],
        'mean_sentiment': [(sample_data['sentiment'].iloc[0] + sample_data['sentiment'].iloc[2]) / 2]
    })
    pd.testing.assert_frame_equal(
        top_companies_sentiment.reset_index(drop=True),
        expected_top_company_sentiment.reset_index(drop=True)
    )


def test_get_daily_sentiment(sample_data):
    cleaned_data = get_clean_data(sample_data)
    top_companies_df = get_average_sentiment_for_top_companies(cleaned_data)
    top_companies = top_companies_df['companies'].tolist()
    daily_sentiment = get_daily_sentiment(cleaned_data, top_companies)
    expected_daily_sentiment = pd.DataFrame({
        'companies': ['Company A', 'Company A', 'Company B'],
        'published': pd.to_datetime(['2024-01-01', '2024-01-03', '2024-01-02']),
        'sentiment': [0.5, 0.7, 0.3]
    })
    pd.testing.assert_frame_equal(
        daily_sentiment.reset_index(drop=True),
        expected_daily_sentiment.reset_index(drop=True)
    )
