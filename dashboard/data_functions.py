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


MISIDENTIFIED_COMPANIES = {
    'AI', 'AI Model', 'AI Language Model', 'API', 'App', 'GPU', 'RAM',
    'Grok', 'Codex', 'Sentinel', 'Model', 'Recursive Intelligence', 'Block Safety', 'Reddit', 'VM', '3D', 'Spark'
}

MISIDENTIFIED_INDIVIDUALS = {
    'Claude', 'Molly', 'Siri', 'Alexa', 'Muse', 'Kepler', 'Sundai',
    'Kyler', 'Will', 'Molly Taft', 'Stretchay', 'Tom', 'Pichard',  'Leesha', 'Max', 'Romanenko', 'Kimi', 'K2',
    'Spencer', 'Kimball', 'Nicholas', 'Tristan', 'Buckmaster'
}


def filter_misidentified_entities(data: pd.DataFrame, exclude_misidentified: bool = True) -> pd.DataFrame:
    """Filter out commonly misidentified entities (AI assistants, voice assistants, etc.).
    
    Args:
        data: Input DataFrame with 'companies' and 'individuals' columns
        exclude_misidentified: If True (default), removes misidentified entities.
                              If False, keeps all entities.
    
    Returns:
        pd.DataFrame: DataFrame with filtered entities
    """
    if not exclude_misidentified or data.empty:
        return data
    
    # Filter companies
    data['companies'] = data['companies'].apply(
        lambda x: [c for c in x if c not in MISIDENTIFIED_COMPANIES] if isinstance(x, list) else x
    )
    
    # Filter individuals
    data['individuals'] = data['individuals'].apply(
        lambda x: [i for i in x if i not in MISIDENTIFIED_INDIVIDUALS] if isinstance(x, list) else x
    )
    
    return data


def get_filtered_data(data: pd.DataFrame, companies: list[str],
                      individuals: list[str], authors: list[str],
                      keywords: list[str], date_range: tuple,
                      sentiment_range: tuple) -> pd.DataFrame:
    """Returns a filtered dataframe"""
    if not data.empty:
        data['companies'] = data['companies'].apply(
            lambda x: [company for company in x if company in companies]
        )

    if not data.empty:
        data['individuals'] = data['individuals'].apply(
            lambda x: [
                individual for individual in x if individual in individuals]
        )

    if not data.empty:
        data['author'] = data['author'].apply(
            lambda x: [author for author in x if author in authors]
        )

    if not data.empty:
        data['tags'] = data['tags'].apply(
            lambda x: [tag for tag in x if tag in keywords]
        )

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


def get_company_wordcloud_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns company mention counts for wordcloud visualization"""
    if data.empty:
        return pd.DataFrame(columns=['companies', 'count'])

    # Explode and filter out empty strings and NaN values
    company_counts = (
        data.explode("companies")
        .dropna(subset=['companies'])
        .query("companies != ''")
        .groupby("companies")
        .size()
        .reset_index(name="count")
    )
    return company_counts.sort_values(by="count", ascending=False)


def get_individual_wordcloud_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns individual mention counts for wordcloud visualization"""
    if data.empty:
        return pd.DataFrame(columns=['individuals', 'count'])

    # Explode and filter out empty strings and NaN values
    individual_counts = (
        data.explode("individuals")
        .dropna(subset=['individuals'])
        .query("individuals != ''")
        .groupby("individuals")
        .size()
        .reset_index(name="count")
    )
    return individual_counts.sort_values(by="count", ascending=False)


def get_companies_over_time(data: pd.DataFrame) -> pd.DataFrame:
    """Returns cumulative company mention counts over time"""
    if data.empty:
        return pd.DataFrame(columns=['published', 'companies', 'count'])

    # Explode companies and count by date
    companies_time = (
        data.explode("companies")
        .dropna(subset=['companies'])
        .query("companies != ''")
        .groupby(['published', 'companies'])
        .size()
        .reset_index(name='daily_count')
    )

    # Sort by date and calculate cumulative sum for each company
    companies_time = companies_time.sort_values('published')
    companies_time['count'] = companies_time.groupby(
        'companies')['daily_count'].cumsum()

    return companies_time[['published', 'companies', 'count']]


def get_individuals_over_time(data: pd.DataFrame) -> pd.DataFrame:
    """Returns cumulative individual mention counts over time"""
    if data.empty:
        return pd.DataFrame(columns=['published', 'individuals', 'count'])

    # Explode individuals and count by date
    individuals_time = (
        data.explode("individuals")
        .dropna(subset=['individuals'])
        .query("individuals != ''")
        .groupby(['published', 'individuals'])
        .size()
        .reset_index(name='daily_count')
    )

    # Sort by date and calculate cumulative sum for each individual
    individuals_time = individuals_time.sort_values('published')
    individuals_time['count'] = individuals_time.groupby('individuals')[
        'daily_count'].cumsum()

    return individuals_time[['published', 'individuals', 'count']]


def get_trending_companies_with_sentiment(data: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Returns trending companies (count > 1) in last N days with average sentiment"""
    if data.empty:
        return pd.DataFrame(columns=['companies', 'count', 'sentiment'])

    # Filter for last N days
    cutoff_date = data['published'].max() - pd.Timedelta(days=days)
    recent_data = data[data['published'] >= cutoff_date]

    if recent_data.empty:
        return pd.DataFrame(columns=['companies', 'count', 'sentiment'])

    # Explode companies and get count and average sentiment
    companies_exploded = recent_data.explode("companies").dropna(
        subset=['companies']).query("companies != ''")

    company_data = companies_exploded.groupby('companies').agg(
        count=('companies', 'size'),
        sentiment=('sentiment', 'mean')
    ).reset_index()

    # Filter for count > 1
    return company_data[company_data['count'] > 1].sort_values(by='count', ascending=False)


def get_trending_individuals_with_sentiment(data: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Returns trending individuals (count > 1) in last N days with average sentiment"""
    if data.empty:
        return pd.DataFrame(columns=['individuals', 'count', 'sentiment'])

    # Filter for last N days
    cutoff_date = data['published'].max() - pd.Timedelta(days=days)
    recent_data = data[data['published'] >= cutoff_date]

    if recent_data.empty:
        return pd.DataFrame(columns=['individuals', 'count', 'sentiment'])

    # Explode individuals and get count and average sentiment
    individuals_exploded = recent_data.explode("individuals").dropna(
        subset=['individuals']).query("individuals != ''")

    individual_data = individuals_exploded.groupby('individuals').agg(
        count=('individuals', 'size'),
        sentiment=('sentiment', 'mean')
    ).reset_index()

    # Filter for count > 1
    return individual_data[individual_data['count'] > 1].sort_values(by='count', ascending=False)


def get_trending_companies(data: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Returns trending companies (count > 1) in the last N days"""
    if data.empty:
        return pd.DataFrame(columns=['companies', 'count'])

    # Filter for last N days
    cutoff_date = data['published'].max() - pd.Timedelta(days=days)
    recent_data = data[data['published'] >= cutoff_date]

    if recent_data.empty:
        return pd.DataFrame(columns=['companies', 'count'])

    # Count companies and filter for count > 1
    company_counts = (
        recent_data.explode("companies")
        .dropna(subset=['companies'])
        .query("companies != ''")
        .groupby("companies")
        .size()
        .reset_index(name='count')
    )

    # Filter for count > 1
    return company_counts[company_counts['count'] > 1].sort_values(by='count', ascending=False)


def get_trending_individuals(data: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Returns trending individuals (count > 1) in the last N days"""
    if data.empty:
        return pd.DataFrame(columns=['individuals', 'count'])

    # Filter for last N days
    cutoff_date = data['published'].max() - pd.Timedelta(days=days)
    recent_data = data[data['published'] >= cutoff_date]

    if recent_data.empty:
        return pd.DataFrame(columns=['individuals', 'count'])

    # Count individuals and filter for count > 1
    individual_counts = (
        recent_data.explode("individuals")
        .dropna(subset=['individuals'])
        .query("individuals != ''")
        .groupby("individuals")
        .size()
        .reset_index(name="count")
    )

    return individual_counts[individual_counts['count'] > 1].sort_values(by="count", ascending=False)
