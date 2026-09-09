"""
Streamlit Dashboard
"""
import logging
import streamlit as st
import altair as alt

from data import (
    get_total_articles,
    get_average_sentiment,
    get_company_mention_count
)


if __name__ == "__main__":

    st.markdown("# Otranto Development: AI Media Analysis")

    # Metrics
    st.markdown("## Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Articles",
            f"{get_total_articles('data')}"
        )
    with col2:
        st.metric(
            "Average Sentiment",
            f"{get_average_sentiment('data')}"
        )
    with col3:
        st.metric(
            "Company Mention Count",
            f"{get_company_mention_count('data')}"
        )
