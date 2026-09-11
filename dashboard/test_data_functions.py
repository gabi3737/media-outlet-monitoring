# pylint: skip-file


import pytest
import pandas as pd

from data_functions import (get_clean_data,
                            get_average_sentiment, get_companies_over_time,
                            get_company_mention_count,
                            get_average_sentiment_by_company,
                            get_average_sentiment_for_top_companies,
                            get_daily_sentiment,
                            get_company_wordcloud_data, get_individual_wordcloud_data, get_individuals_over_time, get_trending_companies, get_trending_companies_with_sentiment, get_trending_individuals, get_trending_individuals_with_sentiment)


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


def test_get_company_wordcloud_data(sample_data):
    cleaned_data = get_clean_data(sample_data)
    company_wordcloud_data = get_company_wordcloud_data(cleaned_data)
    expected_wordcloud_data = pd.DataFrame({
        'companies': ['Company A', 'Company B'],
        'count': [2, 1]
    })
    pd.testing.assert_frame_equal(
        company_wordcloud_data.reset_index(drop=True),
        expected_wordcloud_data.reset_index(drop=True)
    )


def test_get_company_wordcloud_data_empty(sample_data):
    empty = get_company_wordcloud_data(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'companies': (),
        'count': []
    })
    assert empty.empty and empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_individual_wordcloud_data(sample_data):
    cleaned_data = get_clean_data(sample_data)
    individual_wordcloud_data = get_individual_wordcloud_data(cleaned_data)
    expected_individual_wordcloud_data = pd.DataFrame({
        'individuals': ['Person1', 'Person2'],
        'count': [2, 1]
    })
    pd.testing.assert_frame_equal(
        individual_wordcloud_data.reset_index(drop=True),
        expected_individual_wordcloud_data.reset_index(drop=True)
    )


def test_get_individual_wordcloud_data_empty(sample_data):
    empty = get_individual_wordcloud_data(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'individuals': (),
        'count': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_companies_over_time(sample_data):
    cleaned_data = get_clean_data(sample_data)
    companies_over_time = get_companies_over_time(cleaned_data)
    expected_companies_over_time = pd.DataFrame({
        'published': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'companies': ['Company A', 'Company B', 'Company A'],
        'count': [1, 1, 2]
    })
    pd.testing.assert_frame_equal(
        companies_over_time.reset_index(drop=True),
        expected_companies_over_time.reset_index(drop=True)
    )


def test_get_companies_over_time_empty(sample_data):
    empty = get_companies_over_time(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'published': [],
        'companies': [],
        'count': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_individuals_over_time(sample_data):
    cleaned_data = get_clean_data(sample_data)
    individuals_over_time = get_individuals_over_time(cleaned_data)
    expected_individuals_over_time = pd.DataFrame({
        'published': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'individuals': ['Person1', 'Person2', 'Person1'],
        'count': [1, 1, 2]
    })
    pd.testing.assert_frame_equal(
        individuals_over_time.reset_index(drop=True),
        expected_individuals_over_time.reset_index(drop=True)
    )


def test_get_individuals_over_time_empty(sample_data):
    empty = get_individuals_over_time(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'published': [],
        'individuals': [],
        'count': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_trending_companies_with_sentiment(sample_data):
    cleaned_data = get_clean_data(sample_data)
    trending_companies_with_sentiment = get_trending_companies_with_sentiment(
        cleaned_data)
    expected_trending_companies_with_sentiment = pd.DataFrame({
        'companies': ['Company A'],
        'count': [2],
        'sentiment': [0.6]
    })
    pd.testing.assert_frame_equal(
        trending_companies_with_sentiment.reset_index(drop=True),
        expected_trending_companies_with_sentiment.reset_index(drop=True)
    )


def test_get_trending_companies_with_sentiment_empty(sample_data):
    empty = get_trending_companies_with_sentiment(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'companies': [],
        'count': [],
        'sentiment': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_trending_individuals_with_sentiment(sample_data):
    cleaned_data = get_clean_data(sample_data)
    trending_individuals_with_sentiment = get_trending_individuals_with_sentiment(
        cleaned_data)
    expected_trending_individuals_with_sentiment = pd.DataFrame({
        'individuals': ['Person1'],
        'count': [2],
        'sentiment': [0.6]
    })
    pd.testing.assert_frame_equal(
        trending_individuals_with_sentiment.reset_index(drop=True),
        expected_trending_individuals_with_sentiment.reset_index(drop=True)
    )


def test_get_trending_individuals_with_sentiment_empty(sample_data):
    empty = get_trending_individuals_with_sentiment(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'individuals': [],
        'count': [],
        'sentiment': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_trending_companies(sample_data):
    cleaned_data = get_clean_data(sample_data)
    trending_companies = get_trending_companies(cleaned_data)
    expected_trending_companies = pd.DataFrame({
        'companies': ['Company A'],
        'count': [2]
    })
    pd.testing.assert_frame_equal(
        trending_companies.reset_index(drop=True),
        expected_trending_companies.reset_index(drop=True)
    )


def test_get_trending_companies_empty(sample_data):
    empty = get_trending_companies(
        pd.DataFrame(columns=sample_data.columns))
    expected_empty = pd.DataFrame({
        'companies': [],
        'count': []
    })
    assert empty.columns.tolist() == expected_empty.columns.tolist()


def test_get_trending_individuals(sample_data):
    cleaned_data = get_clean_data(sample_data)
    trending_individuals = get_trending_individuals(cleaned_data)
    expected_trending_individuals = pd.DataFrame({
        'individuals': ['Person1'],
        'count': [2]
    })
    pd.testing.assert_frame_equal(
        trending_individuals.reset_index(drop=True),
        expected_trending_individuals.reset_index(drop=True)
    )
