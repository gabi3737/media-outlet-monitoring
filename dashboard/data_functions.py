"""
Functions that manipulate the dataframe for the visualisations
"""
import logging
import pandas as pd


def get_clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a cleaned dataframe"""
    data['published'] = pd.to_datetime(data['published'], errors='coerce')
    data['date'] = data['published'].dt.date
    data['companies'] = (
        data['companies'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )
    data['tags'] = (
        data['tags'].str.replace('[', '')
        .str.replace(']', '').str.replace("'", "")
        .str.split(', ')
    )
    data['individuals'] = (
        data['individuals'].str.replace('[', '')
        .str.replace(']', '').str.split(', ')
    )
    data['author'] = (
        data['author'].str.replace('[', '')
        .str.replace(']', '').str.replace("'", "")
        .str.split(', ')
    )

    return data


def get_filtered_data(data: pd.DataFrame, companies: list[str],
                      individuals: list[str], authors: list[str],
                      keywords: list[str], date_range: tuple,
                      sentiment_range: tuple) -> pd.DataFrame:
    """Returns a filtered dataframe"""
    if not data.empty:
        data = data[data['companies'].apply(
            lambda x: any(company in companies for company in x))]
    if not data.empty:
        data = data[data['individuals'].apply(
            lambda x: any(individual in individuals for individual in x))]
    if not data.empty:
        data = data[data['author'].apply(
                    lambda x: any(author in authors for author in x))]
    if not data.empty:
        data = data[data['tags'].apply(
                    lambda x: any(keyword in keywords for keyword in x))]
    if not data.empty:
        data = data[data['date'].between(
            date_range[0], date_range[1], inclusive='both')]
    if not data.empty:
        data = data[data['sentiment'].between(
            sentiment_range[0], sentiment_range[1], inclusive='both')]

    return data


def get_average_sentiment(data: pd.DataFrame) -> float:
    """Returns the average sentiment"""
    if not data.empty:
        return round(data['sentiment'].mean(), 2)
    else:
        return 0


def get_company_mention_count(data: pd.DataFrame) -> int:
    """Returns the count of companies mentioned"""
    if not data.empty:
        return data["companies"].explode().nunique()
    else:
        return 0
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
