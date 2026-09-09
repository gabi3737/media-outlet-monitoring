"""
The transform aspect of the pipeline
"""
import logging
from datetime import datetime, timezone
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
import spacy.cli


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
    logging.info("Cleaning the author column")
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


def get_sentiment_spacey(nlp: SpacyTextBlob, content: str) -> float:
    """Returns the average sentiment score of an article"""
    logging.info("Adding a sentiment column")
    doc = nlp(content)
    return doc._.blob.polarity


if __name__ == "__main__":

    # Set up:
    logging.basicConfig(level=logging.INFO)

    # Set up for sentiment:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load('en_core_web_sm')
    nlp.add_pipe('spacytextblob')

    # TODO: Make changes to connect to the extract.py later
    # Set up data:
    data = pd.read_csv("pipeline/data/wired_ai_feed.csv")
    # data = pd.read_csv("pipeline/data/venturebeat_ai_feed.csv")

    # Clean data:
    data = clean_publication_time(data)
    data = clean_string_columns(data)
    data = clean_author_column(data)

    # Get sentiment of articles
    data['sentiment'] = data['content'].apply(
        lambda x: get_sentiment_spacey(nlp, x))

    logging.info("Successfully cleaned the dataframe")

    # TODO: Delete before submission
    # Check output:
    with pd.option_context("display.max_colwidth", None):
        print(data['sentiment'].to_string())
