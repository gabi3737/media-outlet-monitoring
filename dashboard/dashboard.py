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
            f"{round(data['sentiment'].mean(), 2)}"
        )
    with col3:
        st.metric(
            "Company Mention Count",
            f"{get_company_mention_count(data)}"
        )

    st.dataframe(data)
    st.markdown(data.dtypes)
