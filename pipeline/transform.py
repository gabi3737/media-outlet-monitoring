"""
The transform aspect of the pipeline
"""
import logging
import pandas as pd
from datetime import datetime


def clean_publication_time(data: pd.DataFrame) -> pd.DataFrame:
    """Returns a dataframe with a cleaned publication time"""
    data['publication_time'] = pd.to_datetime(
        data['publication_time'], errors='coerce')

    data["publication_time"] = data["publication_time"].where(
        data["publication_time"] < datetime.now()
    )

    return data


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
