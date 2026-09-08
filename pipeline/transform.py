"""
The transform aspect of the pipeline
"""
import logging
import pandas as pd
from datetime import datetime, timezone


def clean_publication_time(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe with a cleaned publication time"""
    data['published'] = pd.to_datetime(
        data['published'], errors='coerce', utc=True)

    data["published"] = data["published"].where(
        data["published"] < datetime.now(timezone.utc)
    )

    return data


def clean_string_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe where string columns are all cleaned"""
    data['title'] = data['title'].str.strip()
    data['content'] = data['content'].str.strip()
    data['author'] = data['author'].str.strip().str.capitalize()
    data["tags"] = (
        data["tags"]
        .str.strip()
        .str.lower()
        .str.split(r", | / ")
        .apply(lambda x: list(set(x)))
    )

    return data


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    data = pd.read_csv("pipeline/data/wired_ai_feed.csv")
    # data = pd.read_csv("pipeline/data/venturebeat_ai_feed.csv")

    data = clean_publication_time(data)
    data = clean_string_columns(data)

    with pd.option_context("display.max_colwidth", None):
        print(data.head(1).to_string())
