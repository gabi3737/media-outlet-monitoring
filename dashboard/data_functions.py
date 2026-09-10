"""
Functions that manipulate the dataframe for the visualisations
"""
import logging
import pandas as pd


def get_clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a cleaned dataframe"""
    data['published'] = pd.to_datetime(data['published'], errors='coerce')
    data['companies'] = (
        data['companies'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )

    data['tags'] = (
        data['tags'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )

    data['individuals'] = (
        data['individuals'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )

    data['author'] = (
        data['author'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )

    return data


def get_average_sentiment(data: pd.DataFrame) -> float:
    """Returns the average sentiment"""
    return round(data['sentiment'].mean(), 2)


def get_company_mention_count(data: pd.DataFrame) -> int:
    """Returns the count of companies mentioned"""
    return data["companies"].explode().nunique()


def get_average_sentiment_by_company(data: pd.DataFrame) -> pd.DataFrame:
    """Returns the average sentiment grouped by company"""
    return data.explode("companies").groupby("companies")["sentiment"].mean().round(2).reset_index()
