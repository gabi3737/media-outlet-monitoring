"""
The transform aspect of the pipeline
"""
import os
import logging
from datetime import datetime, timezone
import pandas as pd
import spacy


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


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "data", "venturebeat_ai_feed.csv")

    data = pd.read_csv(csv_path)

    nlp = load_spacy_model()
    data = extract_individuals(data, nlp)
    data = extract_companies(data, nlp)
    data = clean_publication_time(data)
    data = clean_string_columns(data)
    data = clean_author_column(data)

    logging.info("Successfully cleaned the dataframe")

    with pd.option_context("display.max_colwidth", None):
        print(data["individuals"].value_counts())
        print(data["companies"].value_counts())
