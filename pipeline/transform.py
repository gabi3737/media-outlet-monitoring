"""
The transform aspect of the pipeline
"""
import logging
from datetime import datetime, timezone
import pandas as pd


def clean_publication_time(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe with a cleaned publication time"""
    logging.info("Cleaning the published column")
    data['published'] = data['published'].str.replace(
        r"\s+\S+$", "", regex=True
    )

    data['published'] = pd.to_datetime(
        data['published'], errors='coerce', utc=True)

    data["published"] = data["published"].where(
        data["published"] < datetime.now(timezone.utc)
    )

    return data


def clean_string_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe where string columns are all cleaned"""
    logging.info("Cleaning all string columns")
    data['title'] = data['title'].astype(str).str.strip()
    data['content'] = data['content'].astype(str).str.strip()
    data["tags"] = (
        data["tags"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.split(r", | / ")
        .apply(lambda x: list(set(x)) if isinstance(x, list) else [])
    )

    return data


def clean_author_column(data: pd.DataFrame) -> pd.DataFrame:
    """Returns the dataframe with a cleaned author column"""
    data['author'] = (
        data['author']
        .astype(str)
        .str.split(', ')
        .apply(
            lambda authors: [
                author.split('(')[1].split(')')[0].strip().title()
                if '(' in author and ')' in author
                else author.strip().title()
                for author in authors
            ] if isinstance(authors, list) else None
        )
    )

    return data


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    data = pd.read_csv("pipeline/data/wired_ai_feed.csv")
    # data = pd.read_csv("pipeline/data/venturebeat_ai_feed.csv")

    data = clean_publication_time(data)
    data = clean_string_columns(data)
    data = clean_author_column(data)

    logging.info("Successfully cleaned the dataframe")

    with pd.option_context("display.max_colwidth", None):
        print(data['author'].to_string())
