"""
This module provides functions to extract and parse RSS feeds,
convert them into pandas DataFrames, and save them to CSV or JSON files.
"""
import os
import argparse
import logging
import feedparser
import requests
import pandas as pd
from newspaper import Article

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def extract_feed(url):
    """Extract and parse an RSS feed from the given URL."""
    logging.info(f"Extracting feed from: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=10)
    feed = feedparser.parse(response.content)
    logging.info(
        f"Successfully extracted feed with {len(feed.entries)} entries")
    return feed


def scrape_article_content(url):
    """Scrape article content using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        content = ' '.join(article.text.split())
        logging.debug(f"Scraped content from: {url}")
        return content
    except Exception as e:
        logging.warning(f"Failed to scrape {url}: {str(e)}")
        return 'N/A'


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
        logging.debug(f"Processed entry: {entry.get('title', 'N/A')}")
    return pd.DataFrame(data)


def wired_feed_to_dataframe(feed):
    """Convert a parsed RSS feed into a DataFrame, scraping full content for Wired."""
    data = []
    for entry in feed.entries:
        tags = ', '.join([tag['term'] for tag in entry.get('tags', [])])
        link = entry.get('link', 'N/A')

        # Scrape full article content instead of using summary
        if link != 'N/A':
            content = scrape_article_content(link)
        else:
            content = entry.get(
                'summary', 'N/A').replace(',', ';').replace('\n', ' ')

        data.append({
            'title': entry.get('title', 'N/A'),
            'author': entry.get('author', 'N/A'),
            'published': entry.get('published', 'N/A'),
            'link': link,
            'tags': tags if tags else 'N/A',
            'content': content,
        })
        logging.debug(f"Processed entry: {entry.get('title', 'N/A')}")
    return pd.DataFrame(data)


def fetch_and_save(url, filename, format='csv'):
    """Fetch an RSS feed from the given URL, convert it to a DataFrame, and save it to a file."""
    logging.info(f"Processing feed: {url}")
    feed = extract_feed(url)
    df = feed_to_dataframe(feed)
    os.makedirs('data', exist_ok=True)

    if format == 'json':
        df.to_json(f'data/{filename}', orient='records', indent=2)
    else:
        df.to_csv(f'data/{filename}', index=False)

    logging.info(f"Saved {len(df)} entries to data/{filename} ({format})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract AI feeds from RSS sources')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Output format (default: csv)')
    args = parser.parse_args()

    logging.info(f"Starting feed extraction (format: {args.format})")

    ext = f'.{args.format}'
    os.makedirs('data', exist_ok=True)

    # VentureBeat: uses summary
    logging.info("Processing VentureBeat feed")
    feed = extract_feed("https://venturebeat.com/category/ai/feed")
    df = feed_to_dataframe(feed)
    if args.format == 'json':
        df.to_json(
            f'data/venturebeat_ai_feed{ext}', orient='records', indent=2)
    else:
        df.to_csv(f'data/venturebeat_ai_feed{ext}', index=False)
    logging.info(
        f"Saved {len(df)} entries to data/venturebeat_ai_feed{ext} ({args.format})")

    # Wired: scrapes full content
    logging.info("Processing Wired feed")
    feed = extract_feed("https://www.wired.com/feed/tag/ai/latest/rss")
    df = wired_feed_to_dataframe(feed)
    if args.format == 'json':
        df.to_json(f'data/wired_ai_feed{ext}', orient='records', indent=2)
    else:
        df.to_csv(f'data/wired_ai_feed{ext}', index=False)
    logging.info(
        f"Saved {len(df)} entries to data/wired_ai_feed{ext} ({args.format})")

    logging.info("Feed extraction completed successfully")
