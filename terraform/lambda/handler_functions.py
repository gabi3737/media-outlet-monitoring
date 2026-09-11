"""
Functions that query the data and returns values for endpoints
"""
from datetime import date, timedelta
import pandas as pd


def get_clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a cleaned dataframe"""
    if data.empty:
        return data

    data['published'] = pd.to_datetime(data['published'], errors='coerce')
    data['date'] = data['published'].dt.date

    data['companies'] = (
        data['companies'].fillna('')
        .str.replace('[', '', regex=False)
        .str.replace(']', '', regex=False)
        .str.split(', ')
    )
    data['tags'] = (
        data['tags'].fillna('')
        .str.replace('[', '', regex=False)
        .str.replace(']', '', regex=False)
        .str.replace("'", "", regex=False)
        .str.split(', ')
    )
    data['individuals'] = (
        data['individuals'].fillna('')
        .str.replace('[', '', regex=False)
        .str.replace(']', '', regex=False)
        .str.split(', ')
    )
    data['author'] = (
        data['author'].fillna('')
        .str.replace('[', '', regex=False)
        .str.replace(']', '', regex=False)
        .str.replace("'", "", regex=False)
        .str.split(', ')
    )

    return data


def get_individual(data: pd.DataFrame, individual: str) -> dict:
    """Returns all the articles featuring the selected individual"""
    data = get_clean_data(data)
    data = data[data['individuals'].apply(
        lambda x: individual.lower() in [name.lower() for name in x])]
    return data.to_dict(orient='records')


def get_company_from_db(data: pd.DataFrame, company: str) -> dict:
    """Returns all the articles featuring the selected company"""
    data = get_clean_data(data)
    data = data[data['companies'].apply(
        lambda x: company.lower() in [comp.lower() for comp in x])]
    return data.to_dict(orient='records')


def get_average_sentiment(data: pd.DataFrame) -> dict:
    """Returns the average sentiment of the dataset"""
    data = get_clean_data(data)
    if data.empty:
        return {'error': 'Empty dataset'}
    average_sentiment = data['sentiment'].mean()
    return {
        'average_sentiment': average_sentiment
    }


def get_time_period(data: pd.DataFrame, num_days: int) -> pd.DataFrame:
    """Returns the data filtered by the specified time period"""
    data = get_clean_data(data)
    filter_date = date.today() - timedelta(days=num_days)
    data = data[data['date'].apply(lambda x: x >= filter_date)]
    data = data.drop('date', axis='columns')
    return data
