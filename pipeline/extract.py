"""
This module provides functions to extract and parse RSS feeds,
convert them into pandas DataFrames, and save them to CSV or JSON files.
"""
import os
import argparse
import logging
import time
import feedparser
import requests
import pandas as pd
from newspaper import Article
from bs4 import BeautifulSoup

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
    """Scrape article content using newspaper3k with delay to avoid rate limiting."""
    try:
        time.sleep(1)  # Wait 1 second between requests to avoid rate limiting
        article = Article(url)
        article.download()
        article.parse()
        content = ' '.join(article.text.split())
        logging.debug(f"Scraped content from: {url}")
        return content
    except Exception as e:
        logging.warning(f"Failed to scrape {url}: {str(e)}")
        return 'N/A'


def clean_html_content(html_text):
    """Remove HTML tags and clean up content from RSS summaries."""
    if not html_text or html_text == 'N/A':
        return html_text

    soup = BeautifulSoup(html_text, 'html.parser')
    # Get all text and normalize whitespace
    text = soup.get_text(separator=' ', strip=True)
    # Clean up multiple spaces
    text = ' '.join(text.split())
    return text


def feed_to_dataframe(feed, scrape=True):
    """Convert a parsed RSS feed into a pandas DataFrame.

    Args:
        feed: Parsed RSS feed
        scrape: Whether to scrape full article content (True) or use RSS summary (False)
    """
    data = []
    for entry in feed.entries:
        tags = ', '.join([tag['term'] for tag in entry.get('tags', [])])
        link = entry.get('link', 'N/A')

        # Scrape full article content if requested and link exists
        if scrape and link != 'N/A':
            content = scrape_article_content(link)
        else:
            # Use RSS summary as fallback or default, cleaning HTML
            raw_summary = entry.get('summary', 'N/A')
            content = clean_html_content(raw_summary).replace(',', ';')

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


def extract_all_feeds(save_local=False, format='csv'):
    """Extract all feeds and combine into single DataFrame.

    Args:
        save_local: Whether to save to local CSV/JSON files (default: False)
        format: Output format if save_local=True ('csv' or 'json')

    Returns:
        pd.DataFrame: Combined dataframe from all feeds
    """
    logging.info("Extracting all feeds")

    dataframes = []

    # VentureBeat: uses RSS summary (don't scrape to avoid rate limiting)
    logging.info("Processing VentureBeat feed")
    vb_feed = extract_feed("https://venturebeat.com/category/ai/feed")
    vb_df = feed_to_dataframe(vb_feed, scrape=False)
    dataframes.append(vb_df)
    logging.info(f"Extracted {len(vb_df)} entries from VentureBeat")

    # Wired: scrapes full content
    logging.info("Processing Wired feed")
    wired_feed = extract_feed("https://www.wired.com/feed/tag/ai/latest/rss")
    wired_df = feed_to_dataframe(wired_feed, scrape=True)
    dataframes.append(wired_df)
    logging.info(f"Extracted {len(wired_df)} entries from Wired")

    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    logging.info(f"Combined {len(combined_df)} total entries from all sources")

    # Optionally save to local files
    if save_local:
        os.makedirs('data', exist_ok=True)
        ext = f'.{format}'
        if format == 'json':
            combined_df.to_json(
                f'data/combined_ai_feed{ext}', orient='records', indent=2)
        else:
            combined_df.to_csv(f'data/combined_ai_feed{ext}', index=False)
        logging.info(f"Saved combined feed to data/combined_ai_feed{ext}")

    return combined_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract AI feeds from RSS sources')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv',
                        help='Output format (default: csv)')
    parser.add_argument('--save-local', action='store_true',
                        help='Save extracted data to local CSV/JSON files')
    args = parser.parse_args()

    logging.info(f"Starting feed extraction (format: {args.format})")

    # Extract all feeds
    combined_df = extract_all_feeds(
        save_local=args.save_local, format=args.format)

    logging.info("Feed extraction completed successfully")
