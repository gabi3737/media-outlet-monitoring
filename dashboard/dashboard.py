"""
Streamlit Dashboard
"""
import logging
import streamlit as st
import altair as alt
import boto3
import pandas as pd
from datetime import date

from data_functions import (
    get_clean_data,
    get_filtered_data,
    get_average_sentiment,
    get_company_mention_count,
    get_average_sentiment_by_company,
    get_average_sentiment_for_top_companies,
    get_daily_sentiment,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load data from the DynamoDB"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('c25-gabi-db')

    # Scan all items from the table
    response = table.scan()
    items = response.get('Items', [])

    # Handle pagination if there are more items
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    # Convert to DataFrame
    return pd.DataFrame(items)


def company_filter() -> list[str]:
    """Returns a list of filtered companies"""
    companies = data["companies"].explode().dropna().unique()
    selected_companies = st.sidebar.multiselect(
        "Companies:",
        companies,
        default=companies,
        key="company_filter"
    )
    return selected_companies


def individual_filter() -> list[str]:
    """Returns a list of filtered individuals"""
    individuals = data["individuals"].explode().dropna().unique()
    selected_individuals = st.sidebar.multiselect(
        "Individuals:",
        individuals,
        default=individuals,
        key="individual_filter"
    )
    return selected_individuals


def authors_filter() -> list[str]:
    """Returns a list of filtered authors"""
    authors = data["author"].explode().dropna().unique()
    selected_authors = st.sidebar.multiselect(
        "Authors:",
        authors,
        default=authors,
        key="authors_filter"
    )
    return selected_authors


def keyword_filter() -> list[str]:
    """Returns a list of filtered key words"""
    keywords = data["tags"].explode().dropna().unique()
    selected_tags = st.sidebar.multiselect(
        "Key Words:",
        keywords,
        default=keywords,
        key="tags_filter"
    )
    return selected_tags


def date_filter() -> tuple:
    """Returns a tuple with start and end date"""
    date_range = st.date_input(
        "Select the date range:",
        (date(2026, 1, 1), date.today()),
        date(2026, 1, 1),
        date.today(),
        format="DD/MM/YYYY",
    )
    return date_range


def sentiment_filter() -> tuple:
    """Returns a tuple with the min and max sentiment values"""
    sentiment_range = st.slider(
        "Select the sentiment range:",
        min_value=-1.0,
        max_value=1.0,
        value=[-1.0, 1.0]
    )
    return sentiment_range


def company_chart_by_sentiment(data: pd.DataFrame) -> alt.Chart:
    """Generate a bar chart for top ten companies with greatest sentiment."""
    return alt.Chart(get_average_sentiment_by_company(data).head(10)).mark_bar().encode(
        x=alt.X('companies', title='Company'),
        y=alt.Y('sentiment', title='Average Sentiment'),
        tooltip=['companies', 'sentiment'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
    )


def sentiment_chart_by_company(data: pd.DataFrame) -> alt.Chart:
    """Generate a bar chart for top ten companies by sentiment"""
    return alt.Chart(get_average_sentiment_for_top_companies(data).head(10)).mark_bar().encode(
        x=alt.X('companies', title='Company'),
        y=alt.Y('mean_sentiment', title='Average Sentiment'),
        tooltip=['companies', 'mean_sentiment', 'count'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
    )


def top_ten_companies_daily_sentiment(data: pd.DataFrame) -> alt.Chart:
    """Generate a line chart for top ten companies' daily sentiment."""
    top_companies = get_average_sentiment_for_top_companies(data).head(10)[
        'companies']
    daily_sentiment = get_daily_sentiment(data, top_companies)
    return alt.Chart(daily_sentiment).mark_line().encode(
        x=alt.X('published', title='Date'),
        y=alt.Y('sentiment', title='Average Sentiment'),
        color=alt.Color('companies', scale=alt.Scale(scheme='tableau10')),
        tooltip=['companies', 'published', 'sentiment']
    )


if __name__ == "__main__":

    # Set up data:
    data = load_data()
    data = get_clean_data(data)

    # Streamlit:
    st.markdown("# Otranto Development: AI Media Analysis")

    # Side Bar
    with st.sidebar:
        st.markdown("## Filters")
        selected_companies = company_filter()
        selected_individuals = individual_filter()
        selected_authors = authors_filter()
        selected_tags = keyword_filter()
        date_range = date_filter()
        sentiment_range = sentiment_filter()

    # Filter data:
    data = get_filtered_data(data, selected_companies, selected_individuals,
                             selected_authors, selected_tags, date_range,
                             sentiment_range)

    # Metrics
    st.markdown("## Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Articles",
            len(data)
        )
    with col2:
        st.metric(
            "Average Sentiment",
            get_average_sentiment(data)
        )
    with col3:
        st.metric(
            "Company Mention Count",
            get_company_mention_count(data)
        )

    st.markdown("## Sentiment Analysis")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top 10 Companies with Highest Sentiment")
        st.altair_chart(company_chart_by_sentiment(data), width='stretch')

    with col2:
        st.markdown("#### Top 10 Companies by Sentiment")
        st.altair_chart(sentiment_chart_by_company(data), width='stretch')

    st.markdown("## Top 10 Companies Sentiment Over Time")
    st.altair_chart(top_ten_companies_daily_sentiment(data), width='stretch')

    st.dataframe(data)
