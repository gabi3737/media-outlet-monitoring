"""
Streamlit Dashboard
"""
import logging
import streamlit as st
import altair as alt
import boto3
import pandas as pd
from wordcloud import WordCloud
from datetime import date
import matplotlib.pyplot as plt

from data_functions import (
    get_clean_data,
    get_filtered_data,
    filter_misidentified_entities,
    get_average_sentiment,
    get_company_mention_count,
    get_average_sentiment_by_company,
    get_average_sentiment_for_top_companies,
    get_daily_sentiment,
    get_company_wordcloud_data,
    get_individual_wordcloud_data,
    get_companies_over_time,
    get_individuals_over_time,
    get_trending_companies_with_sentiment,
    get_trending_individuals_with_sentiment,
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
        x=alt.X('companies', title='Company', sort='-y'),
        y=alt.Y('sentiment', title='Average Sentiment'),
        tooltip=['companies', 'sentiment'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
    )


def sentiment_chart_by_company(data: pd.DataFrame) -> alt.Chart:
    """Generate a bar chart for top ten companies by sentiment"""
    return alt.Chart(get_average_sentiment_for_top_companies(data).head(10)).mark_bar().encode(
        x=alt.X('companies', title='Company', sort='-y'),
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


def company_wordcloud_traditional(data: pd.DataFrame):
    """Generate a traditional wordcloud for company mentions using wordcloud library."""
    company_data = get_company_wordcloud_data(data)

    if company_data.empty:
        st.write("No data available for wordcloud")
        return

    # Create a dictionary of company: count
    word_freq = dict(zip(company_data['companies'], company_data['count']))

    # Generate wordcloud
    wordcloud = WordCloud(
        width=1200,
        height=400,
        background_color='black',
        colormap='Greens',
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(word_freq)

    # Display using matplotlib
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def individual_wordcloud_traditional(data: pd.DataFrame):
    """Generate a traditional wordcloud for individuals using wordcloud library."""
    individual_data = get_individual_wordcloud_data(data)

    if individual_data.empty:
        st.write("No data available for wordcloud")
        return

    # Create a dictionary of individual: count
    word_freq = dict(
        zip(individual_data['individuals'], individual_data['count']))

    # Generate wordcloud
    wordcloud = WordCloud(
        width=1200,
        height=400,
        background_color='black',
        colormap='Purples',
        relative_scaling=0.5,
        min_font_size=10
    ).generate_from_frequencies(word_freq)

    # Display using matplotlib
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def companies_mentions_over_time(data: pd.DataFrame) -> alt.Chart:
    """Generate a scatter plot for trending companies with sentiment vs mention count."""
    companies_data = get_trending_companies_with_sentiment(data, days=7)

    if companies_data.empty:
        return None

    return alt.Chart(companies_data).mark_circle(size=200).encode(
        x=alt.X('count', title='Mentions (Last 7 Days)'),
        y=alt.Y('sentiment', title='Average Sentiment'),
        tooltip=['companies', 'count', 'sentiment'],
        color=alt.Color('sentiment', scale=alt.Scale(scheme='redyellowgreen'))
    ).properties(
        height=400,
        width=600
    )


def individuals_mentions_over_time(data: pd.DataFrame) -> alt.Chart:
    """Generate a scatter plot for trending individuals with sentiment vs mention count."""
    individuals_data = get_trending_individuals_with_sentiment(data, days=7)

    if individuals_data.empty:
        return None

    return alt.Chart(individuals_data).mark_circle(size=200).encode(
        x=alt.X('count', title='Mentions (Last 7 Days)'),
        y=alt.Y('sentiment', title='Average Sentiment'),
        tooltip=['individuals', 'count', 'sentiment'],
        color=alt.Color('sentiment', scale=alt.Scale(scheme='redyellowgreen'))
    ).properties(
        height=400,
        width=600
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

        st.markdown("---")
        exclude_misidentified = st.checkbox(
            "🤖 Exclude AI assistants & voice assistants",
            value=True,
            help="Filter out commonly misidentified entities like 'Claude', 'Siri', 'Grok', 'AI', etc. These are often false positives from the NER model."
        )

    # Filter data:
    data = get_filtered_data(data, selected_companies, selected_individuals,
                             selected_authors, selected_tags, date_range,
                             sentiment_range)

    # Apply misidentified entity filter
    data = filter_misidentified_entities(
        data, exclude_misidentified=exclude_misidentified)

    # Metrics
    st.markdown("## Overview")
    st.write("Summary statistics for the selected date range and filters.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Articles",
            len(data),
            help="Total number of articles matching the selected filters"
        )
    with col2:
        avg_sentiment = get_average_sentiment(data)
        st.metric(
            "Average Sentiment",
            f"{avg_sentiment:.2f}",
            help="Average sentiment score across all articles (-1.0 = negative, 1.0 = positive). Calculated using TextBlob polarity analysis."
        )
    with col3:
        st.metric(
            "Company Mentions",
            get_company_mention_count(data),
            help="Total number of company mentions extracted using named entity recognition (NER)"
        )

    st.markdown("## Trends & Frequency")
    st.write(
        "Entity frequency analysis from extracted named entities in article content.")

    with st.expander("🏢 Top Companies", expanded=True):
        st.write("**Size represents mention frequency** — Larger company names appear more frequently in articles. Extracted using spaCy named entity recognition (ORG label).")
        wordcloud_fig = company_wordcloud_traditional(data)
        if wordcloud_fig:
            st.pyplot(wordcloud_fig, use_container_width=True)

    with st.expander("👤 Top Individuals", expanded=True):
        st.write("**Size represents mention frequency** — Larger individual names appear more frequently in articles. Extracted using spaCy named entity recognition (PERSON label).")
        individual_wordcloud_fig = individual_wordcloud_traditional(data)
        if individual_wordcloud_fig:
            st.pyplot(individual_wordcloud_fig, use_container_width=True)

    with st.expander("📈 Trending Companies (Last 7 Days)", expanded=True):
        st.write("**X-axis:** Mention count in the last 7 days | **Y-axis:** Average sentiment | **Color:** Sentiment intensity (red = negative, green = positive). This identifies companies gaining media attention and their associated sentiment.")
        companies_chart = companies_mentions_over_time(data)
        if companies_chart:
            st.altair_chart(companies_chart, use_container_width=True)
        else:
            st.info("No trending data available for the selected filters.")

    with st.expander("📈 Trending Individuals (Last 7 Days)", expanded=True):
        st.write("**X-axis:** Mention count in the last 7 days | **Y-axis:** Average sentiment | **Color:** Sentiment intensity (red = negative, green = positive). This identifies individuals gaining media attention and their associated sentiment.")
        individuals_chart = individuals_mentions_over_time(data)
        if individuals_chart:
            st.altair_chart(individuals_chart, use_container_width=True)
        else:
            st.info("No trending data available for the selected filters.")

    st.markdown("## Sentiment Analysis")
    st.write(
        "Understand how companies and individuals are portrayed across media outlets.")

    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown("### Top 10 Companies by Sentiment")
            st.write("Average sentiment score for the 10 companies with the highest average sentiment across all articles. Calculated as the mean polarity score of all articles mentioning each company.")
            st.altair_chart(company_chart_by_sentiment(data), width='stretch')

    with col2:
        with st.container():
            st.markdown("### Top 10 Most Mentioned Companies (by sentiment)")
            st.write("Average sentiment for the 10 most frequently mentioned companies. Shows how the most talked-about companies are being portrayed in media.")
            st.altair_chart(sentiment_chart_by_company(data), width='stretch')

    with st.expander("📊 Top 10 Companies: Daily Sentiment Trend", expanded=False):
        st.write("**Time series of sentiment scores** for the 10 most frequently mentioned companies. Hover over points to see exact dates and sentiment values. Useful for tracking sentiment changes over time.")
        st.altair_chart(top_ten_companies_daily_sentiment(
            data), width='stretch')

    with st.expander("📋 Raw Data Exploration", expanded=False):
        st.write("View and download the complete filtered dataset. Columns include extracted entities (companies, individuals), sentiment scores, publication date, and source metadata.")
        st.dataframe(data, use_container_width=True)

        # Add CSV download button
        csv = data.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="media_analysis.csv",
            mime="text/csv"
        )
