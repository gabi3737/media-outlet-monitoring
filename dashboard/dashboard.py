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
    get_average_sentiment_by_company

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
    """Generate a sentiment chart grouped by company."""
    return alt.Chart(get_average_sentiment_by_company(data).sort_values(by="sentiment", ascending=False).head(10)).mark_bar().encode(
        x='companies',
        y='sentiment',
        tooltip=['companies', 'sentiment'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
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

    st.markdown("#### Top 10 Companies with Highest Sentiment")
    st.altair_chart(company_chart_by_sentiment(data), use_container_width=True)

    st.dataframe(data)
