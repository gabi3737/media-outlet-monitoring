"""
This module provides functions to extract and parse RSS feeds,
convert them into pandas DataFrames, and save them to CSV or JSON files.
"""
import os
import argparse
import feedparser
import requests
import pandas as pd


def extract_feed(url):
    """Extract and parse an RSS feed from the given URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=10)
    return feedparser.parse(response.content)


def feed_to_dataframe(feed):
    """Convert a parsed RSS feed into a pandas DataFrame."""
    data = []
    for entry in feed.entries:
        tags = ', '.join([tag['term'] for tag in entry.get('tags', [])])
        content = entry.get('summary', 'N/A').replace(',',
                                                      ';').replace('\n', ' ')
        data.append({
            'title': entry.get('title', 'N/A'),
            'author': entry.get('author', 'N/A'),
            'published': entry.get('published', 'N/A'),
            'link': entry.get('link', 'N/A'),
            'tags': tags if tags else 'N/A',
            'content': content,
        })
    return pd.DataFrame(data)


def fetch_and_save(url, filename, format='csv'):
    """Fetch an RSS feed from the given URL, convert it to a DataFrame, and save it to a file."""

    feed = extract_feed(url)
    df = feed_to_dataframe(feed)
    os.makedirs('data', exist_ok=True)

    if format == 'json':
        df.to_json(f'data/{filename}', orient='records', indent=2)
    else:
        df.to_csv(f'data/{filename}', index=False)

    print(df)
    print(f"\nSaved {len(df)} entries to data/{filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract AI feeds from RSS sources')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Output format (default: csv)')
    args = parser.parse_args()

    # Determine file extension based on format
    ext = f'.{args.format}'

    fetch_and_save("https://venturebeat.com/category/ai/feed",
                   f"venturebeat_ai_feed{ext}", args.format)
    fetch_and_save("https://www.wired.com/feed/tag/ai/latest/rss",
                   f"wired_ai_feed{ext}", args.format)
