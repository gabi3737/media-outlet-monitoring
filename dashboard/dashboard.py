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
    get_average_sentiment,
    get_company_mention_count
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


if __name__ == "__main__":

    # Set up data:
    data = load_data()
    data = get_clean_data(data)

    # Streamlit:
    st.markdown("# Otranto Development: AI Media Analysis")

    # Side Bar
    with st.sidebar:
        st.markdown("## Filters")
        companies = data["companies"].explode().dropna().unique()
        selected_companies = st.sidebar.multiselect(
            "Companies:",
            companies,
            default=companies,
            key="company_filter"
        )

        individuals = data["individuals"].explode().dropna().unique()
        selected_individuals = st.sidebar.multiselect(
            "Individuals:",
            individuals,
            default=individuals,
            key="individual_filter"
        )

        authors = data["author"].explode().dropna().unique()
        selected_authors = st.sidebar.multiselect(
            "Authors:",
            authors,
            default=authors,
            key="authors_filter"
        )

        key_words = data["tags"].explode().dropna().unique()
        selected_tags = st.sidebar.multiselect(
            "Key Words:",
            key_words,
            default=key_words,
            key="tags_filter"
        )

        date_range = st.date_input(
            "Select the date range:",
            (date(2026, 1, 1), date.today()),
            date(2026, 1, 1),
            date.today(),
            format="DD/MM/YYYY",
        )

        sentiment_range = st.slider(
            "Select the sentiment range:",
            min_value=-1.0,
            max_value=1.0,
            value=[-1.0, 1.0]
        )

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

    st.dataframe(data)
