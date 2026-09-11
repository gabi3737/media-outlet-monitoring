"""
Functions that query the data and returns values for endpoints
"""
import pandas as pd
from datetime import date, timedelta


def get_individual(data: pd.DataFrame, individual: str) -> dict:
    """Returns all the articles featuring the selected individual"""
    data = data[data['individuals'].apply(
        lambda x: individual.lower() in x)]
    return data.to_dict()


def get_company(data: pd.DataFrame, company: str) -> dict:
    """Returns all the articles featuring the selected company"""
    data = data[data['companies'].apply(
        lambda x: company.lower() in x)]
    return data.to_dict()


def get_average_sentiment(data: pd.DataFrame) -> dict:
    """Returns the average sentiment of the dataset"""
    if data.empty:
        return {'error': 'Empty dataset'}
    average_sentiment = data['sentiment'].mean()
    return {
        'average_sentiment': average_sentiment
    }


def get_time_period(data: pd.DataFrame, num_days: int) -> dict:
    """Returns the average sentiment of the dataset"""
    data['published'] = pd.to_datetime(data['published'], errors='coerce')
    data['date'] = data['published'].dt.date
    filter_date = date.today() - timedelta(days=num_days)
    data = data[data['date'].apply(lambda x: x >= filter_date)]
    data = data.drop('date', axis='columns')
    return data.to_dict()
