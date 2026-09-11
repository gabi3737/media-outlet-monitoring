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
    selected_companies = st.multiselect(
        "Companies:",
        companies,
        default=companies,
        key="company_filter"
    )
    return selected_companies


def individual_filter() -> list[str]:
    """Returns a list of filtered individuals"""
    individuals = data["individuals"].explode().dropna().unique()
    selected_individuals = st.multiselect(
        "Individuals:",
        individuals,
        default=individuals,
        key="individual_filter"
    )
    return selected_individuals


def authors_filter() -> list[str]:
    """Returns a list of filtered authors"""
    authors = data["author"].explode().dropna().unique()
    selected_authors = st.multiselect(
        "Authors:",
        authors,
        default=authors,
        key="authors_filter"
    )
    return selected_authors


def keyword_filter() -> list[str]:
    """Returns a list of filtered key words"""
    keywords = data["tags"].explode().dropna().unique()
    selected_tags = st.multiselect(
        "Key Words:",
        keywords,
        default=keywords,
        key="tags_filter"
    )
    return selected_tags


def date_filter() -> tuple:
    """Returns a tuple with start and end date"""
    date_range = st.sidebar.date_input(
        "Select the date range:",
        (date(2026, 1, 1), date.today()),
        date(2026, 1, 1),
        date.today(),
        format="DD/MM/YYYY",
    )
    return date_range


def sentiment_filter() -> tuple:
    """Returns a tuple with the min and max sentiment values"""
    sentiment_range = st.sidebar.slider(
        "Select the sentiment range, where -1 is very negative and 1 is very positive:",
        min_value=-1.0,
        max_value=1.0,
        value=[-1.0, 1.0]
    )
    return sentiment_range


def format_sentiment(value: float) -> str:
    """Convert sentiment value (-1 to 1) to percentage format (+/-X%)"""
    if pd.isna(value):
        return "N/A"
    percentage = int(value * 100)
    if percentage >= 0:
        return f"+{percentage}%"
    else:
        return f"{percentage}%"


def company_chart_by_sentiment(data: pd.DataFrame) -> alt.Chart:
    """Generate a bar chart for top ten companies with greatest sentiment."""
    chart_data = get_average_sentiment_by_company(data).head(10).copy()
    chart_data['sentiment_pct'] = chart_data['sentiment'].apply(
        format_sentiment)
    return alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('companies', title='Company', sort='-y'),
        y=alt.Y('sentiment', title='Average Sentiment',
                axis=alt.Axis(format='.0%')),
        tooltip=['companies', 'sentiment_pct'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
    )


def sentiment_chart_by_company(data: pd.DataFrame) -> alt.Chart:
    """Generate a bar chart for top ten companies by sentiment"""
    chart_data = get_average_sentiment_for_top_companies(data).head(10).copy()
    chart_data['mean_sentiment_pct'] = chart_data['mean_sentiment'].apply(
        format_sentiment)
    return alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('companies', title='Company', sort='-y'),
        y=alt.Y('mean_sentiment', title='Average Sentiment',
                axis=alt.Axis(format='.0%')),
        tooltip=['companies', 'mean_sentiment_pct', 'count'],
        color=alt.Color('companies', scale=alt.Scale(
            scheme='tableau10'), legend=None)
    )


def top_ten_companies_daily_sentiment(data: pd.DataFrame) -> alt.Chart:
    """Generate a line chart for top ten companies' daily sentiment."""
    top_companies = get_average_sentiment_for_top_companies(data).head(10)[
        'companies']
    daily_sentiment = get_daily_sentiment(data, top_companies).copy()
    daily_sentiment['sentiment_pct'] = daily_sentiment['sentiment'].apply(
        format_sentiment)
    return alt.Chart(daily_sentiment).mark_line().encode(
        x=alt.X('published', title='Date'),
        y=alt.Y('sentiment', title='Average Sentiment',
                axis=alt.Axis(format='.0%')),
        color=alt.Color('companies', scale=alt.Scale(scheme='tableau10')),
        tooltip=['companies', 'published', 'sentiment_pct']
    )


def sentiment_to_color(sentiment, min_sentiment=None, max_sentiment=None):
    """Convert sentiment value to a color based on relative position in range.

    Args:
        sentiment: Value between -1 (negative) and 1 (positive)
        min_sentiment: Minimum sentiment value in the dataset (for normalization)
        max_sentiment: Maximum sentiment value in the dataset (for normalization)

    Returns:
        Color string: red for negative, yellow for neutral, green for positive
    """
    # If we have min/max, normalize to that range
    if min_sentiment is not None and max_sentiment is not None:
        if max_sentiment != min_sentiment:
            normalized = (sentiment - min_sentiment) / \
                (max_sentiment - min_sentiment)
        else:
            normalized = 0.5
    else:
        # Otherwise normalize to standard -1 to 1 range
        normalized = (sentiment + 1) / 2

    # Clamp to 0-1
    normalized = max(0, min(1, normalized))

    # Use color spectrum: red (0) -> yellow (0.5) -> green (1)
    if normalized < 0.25:
        return "#d7191c"  # Dark red
    elif normalized < 0.4:
        return "#fdae61"  # Orange
    elif normalized < 0.6:
        return "#ffffbf"  # Yellow
    elif normalized < 0.75:
        return "#a6d96a"  # Light green
    else:
        return "#1a9641"  # Dark green


def company_wordcloud_traditional(data: pd.DataFrame):
    """Generate a wordcloud for company mentions colored by sentiment."""
    company_data = get_company_wordcloud_data(data)

    if company_data.empty:
        st.write("No data available for wordcloud")
        return

    # Get sentiment for each company
    sentiment_df = get_average_sentiment_by_company(data)
    sentiment_by_company = sentiment_df.set_index(
        'companies')['sentiment'].to_dict()

    # Calculate min/max for normalization
    min_sent = sentiment_df['sentiment'].min()
    max_sent = sentiment_df['sentiment'].max()

    # Create a dictionary of company: count
    word_freq = dict(zip(company_data['companies'], company_data['count']))

    # Create color function that uses sentiment with dynamic normalization
    def color_func(word, **kwargs):
        sentiment = sentiment_by_company.get(word, 0)
        return sentiment_to_color(sentiment, min_sent, max_sent)

    # Generate wordcloud with sentiment-based coloring
    wordcloud = WordCloud(
        width=1200,
        height=400,
        background_color='black',
        relative_scaling=0.5,
        min_font_size=10,
        color_func=color_func
    ).generate_from_frequencies(word_freq)

    # Display using matplotlib
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def individual_wordcloud_traditional(data: pd.DataFrame):
    """Generate a wordcloud for individuals colored by sentiment."""
    individual_data = get_individual_wordcloud_data(data)

    if individual_data.empty:
        st.write("No data available for wordcloud")
        return

    # Get sentiment for each individual
    sentiment_data = data.explode('individuals').dropna(subset=['individuals'])
    sentiment_by_individual = sentiment_data.groupby(
        'individuals')['sentiment'].mean().to_dict()

    # Calculate min/max for normalization
    min_sent = min(sentiment_by_individual.values())
    max_sent = max(sentiment_by_individual.values())

    # Create a dictionary of individual: count
    word_freq = dict(
        zip(individual_data['individuals'], individual_data['count']))

    # Create color function that uses sentiment with dynamic normalization
    def color_func(word, **kwargs):
        sentiment = sentiment_by_individual.get(word, 0)
        return sentiment_to_color(sentiment, min_sent, max_sent)

    # Generate wordcloud with sentiment-based coloring
    wordcloud = WordCloud(
        width=1200,
        height=400,
        background_color='black',
        relative_scaling=0.5,
        min_font_size=10,
        color_func=color_func
    ).generate_from_frequencies(word_freq)

    # Display using matplotlib
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig


def companies_mentions_over_time(data: pd.DataFrame) -> alt.Chart:
    """Generate a scatter plot for trending companies with sentiment vs mention count."""
    companies_data = get_trending_companies_with_sentiment(data, days=7).copy()

    if companies_data.empty:
        return None

    companies_data['sentiment_pct'] = companies_data['sentiment'].apply(
        format_sentiment)
    return alt.Chart(companies_data).mark_circle(size=200).encode(
        x=alt.X('count', title='Mentions (Last 7 Days)',
                axis=alt.Axis(format='d')),
        y=alt.Y('sentiment', title='Average Sentiment',
                axis=alt.Axis(format='.0%')),
        tooltip=['companies', 'count', 'sentiment_pct'],
        color=alt.Color('sentiment', scale=alt.Scale(scheme='redyellowgreen'))
    ).properties(
        height=400,
        width=600
    )


def individuals_mentions_over_time(data: pd.DataFrame) -> alt.Chart:
    """Generate a scatter plot for trending individuals with sentiment vs mention count."""
    individuals_data = get_trending_individuals_with_sentiment(
        data, days=7).copy()

    if individuals_data.empty:
        return None

    individuals_data['sentiment_pct'] = individuals_data['sentiment'].apply(
        format_sentiment)
    return alt.Chart(individuals_data).mark_circle(size=200).encode(
        x=alt.X('count', title='Mentions (Last 7 Days)',
                axis=alt.Axis(format='d')),
        y=alt.Y('sentiment', title='Average Sentiment',
                axis=alt.Axis(format='.0%')),
        tooltip=['individuals', 'count', 'sentiment_pct'],
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

        # Main filters (always visible)
        date_range = date_filter()
        sentiment_range = sentiment_filter()

        # Entity filters (in expander)
        with st.expander("📊 Entity Filters (Companies, Individuals, Authors, Keywords)", expanded=False):
            selected_companies = company_filter()
            selected_individuals = individual_filter()
            selected_authors = authors_filter()
            selected_tags = keyword_filter()

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
            format_sentiment(avg_sentiment),
            help="Average sentiment score as a deviation from neutral. Calculated using TextBlob polarity analysis."
        )
    with col3:
        st.metric(
            "Companies Mentioned",
            get_company_mention_count(data),
            help="Total number of company mentions extracted using named entity recognition (NER)"
        )

    st.markdown("## Trends & Frequency")
    st.write(
        "Entity frequency analysis from extracted named entities in article content.")

    with st.expander("🏢 Top Companies", expanded=True):
        st.write("**Size represents mention frequency** — Larger company names appear more frequently in articles. **Color represents sentiment:** red = negative, yellow = neutral, green = positive (based on average sentiment of articles mentioning each company). Extracted using spaCy named entity recognition (ORG label).")
        wordcloud_fig = company_wordcloud_traditional(data)
        if wordcloud_fig:
            st.pyplot(wordcloud_fig, use_container_width=True)

    with st.expander("👤 Top Individuals", expanded=True):
        st.write("**Size represents mention frequency** — Larger individual names appear more frequently in articles. **Color represents sentiment:** red = negative, yellow = neutral, green = positive (based on average sentiment of articles mentioning each individual). Extracted using spaCy named entity recognition (PERSON label).")
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
