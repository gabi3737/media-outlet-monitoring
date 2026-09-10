"""
Streamlit Dashboard
"""
import logging
import streamlit as st
import altair as alt
import boto3
import pandas as pd

from data_functions import (
    get_clean_data,
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
