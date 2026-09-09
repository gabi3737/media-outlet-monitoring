"""
The transform aspect of the pipeline
"""
import os
import logging
from datetime import datetime, timezone
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

# Import extract module for standalone testing
from extract import extract_all_feeds


def load_spacy_model():
    """Load a spacy model for named entity recognition."""
    from spacy.cli import download

    model_name = "en_core_web_md"

    try:
        nlp = spacy.load(model_name)
        logging.info(f"Successfully loaded spacy model: {model_name}")
        return nlp
    except OSError:
        logging.warning(f"Spacy model not found. Downloading {model_name}...")
        download(model_name)
        nlp = spacy.load(model_name)
        logging.info(
            f"Successfully downloaded and loaded spacy model: {model_name}")
        return nlp


def extract_individuals(data: pd.DataFrame, nlp) -> pd.DataFrame:
    """Extract people entities from article content using spacy NER."""
    logging.info("Extracting individuals from content")

    individuals_list = []
    for content in data['content']:
        if isinstance(content, str) and content != 'N/A':
            doc = nlp(content)
            # Extract PERSON entities
            people = list(
                set([ent.text for ent in doc.ents if ent.label_ == "PERSON"]))
            individuals_list.append(', '.join(people) if people else 'N/A')
        else:
            individuals_list.append('N/A')

    data['individuals'] = individuals_list
    logging.info(
        f"Successfully extracted individuals for {len(data)} articles")
    return data


def extract_companies(data: pd.DataFrame, nlp) -> pd.DataFrame:
    """Extract company entities from article content using spacy NER."""
    logging.info("Extracting companies from content")

    companies_list = []
    for content in data['content']:
        if isinstance(content, str) and content != 'N/A':
            doc = nlp(content)
            # Extract ORG entities
            companies = list(
                set([ent.text for ent in doc.ents if ent.label_ == "ORG"]))
            companies_list.append(', '.join(companies) if companies else 'N/A')
        else:
            companies_list.append('N/A')

    data['companies'] = companies_list
    logging.info(
        f"Successfully extracted companies for {len(data)} articles")
    return data


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
    """Returns the dataframe with a cleaned author column."""
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


def get_sentiment(nlp: SpacyTextBlob, content: str) -> float:
    """Returns the sentiment score of an article content."""
    doc = nlp(content)
    return doc._.blob.polarity


def extract_sentiment(data: pd.DataFrame, nlp) -> pd.DataFrame:
    """Extract sentiment scores from article content using spacytextblob."""
    logging.info("Extracting sentiment from content")
    data['sentiment'] = data['content'].apply(lambda x: get_sentiment(nlp, x))
    logging.info(f"Successfully extracted sentiment for {len(data)} articles")
    return data


def transform_data(data: pd.DataFrame) -> pd.DataFrame:
    """Apply all transformations to the data pipeline.

    Args:
        data: Input DataFrame from extract_all_feeds()

    Returns:
        pd.DataFrame: Fully transformed data ready for loading
    """
    logging.info(f"Starting transformation pipeline on {len(data)} rows")
    nlp = load_spacy_model()
    nlp.add_pipe('spacytextblob')

    # Extract entities
    data = extract_individuals(data, nlp)
    data = extract_companies(data, nlp)
    data = extract_sentiment(data, nlp)

    # Clean data
    data = clean_publication_time(data)
    data = clean_string_columns(data)
    data = clean_author_column(data)

    logging.info("Transformation pipeline completed successfully")
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Extract data from feeds
    logging.info("Extracting data from RSS feeds...")
    data = extract_all_feeds()

    # Transform the data
    logging.info("Transforming data...")
    data = transform_data(data)

    logging.info("Successfully completed transform pipeline")

    # Display sample results
    with pd.option_context("display.max_colwidth", None):
        print("\n=== INDIVIDUALS EXTRACTED ===")
        print(data["individuals"].value_counts())
        print("\n=== COMPANIES EXTRACTED ===")
        print(data["companies"].value_counts())
        print("\n=== SENTIMENT SCORES ===")
        print(data['sentiment'].describe())
