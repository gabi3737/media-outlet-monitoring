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
    return data.explode("companies").groupby("companies")["sentiment"].mean().round(2).reset_index().sort_values(by="sentiment", ascending=False)


def get_average_sentiment_for_top_companies(data: pd.DataFrame) -> pd.DataFrame:
    """Returns the average sentiment for the top companies by mention count"""
    counts = data.explode("companies").groupby(
        "companies").size().reset_index(name="count")
    means = data.explode("companies").groupby("companies")[
        "sentiment"].mean().round(2).reset_index(name="mean_sentiment")
    return counts.merge(means, on="companies").sort_values(by="count", ascending=False)


def get_daily_sentiment(data: pd.DataFrame, top_companies: list) -> pd.DataFrame:
    """Returns the daily sentiment for the top companies"""
    return (
        data.explode("companies")
        .query("companies in @top_companies")
        .groupby(["companies", "published"])
        ["sentiment"]
        .mean()
        .reset_index()
    )
