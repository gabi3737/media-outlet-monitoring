# pylint: skip-file

from unittest.mock import MagicMock, patch

from extract import (
    extract_feed,
    feed_to_dataframe,
    scrape_article_content,
    clean_html_content,
)


@patch("extract.feedparser.parse")
@patch("extract.requests.get")
def test_extract_feed_returns_parsed_feed(mock_get, mock_parse):
    mock_response = MagicMock()
    mock_response.content = b"<rss>fake content</rss>"
    mock_get.return_value = mock_response

    mock_feed = MagicMock()
    mock_feed.entries = [{"title": "Entry 1"}, {"title": "Entry 2"}]
    mock_parse.return_value = mock_feed

    result = extract_feed("https://example.com/feed")

    assert result is mock_feed
    assert len(result.entries) == 2


@patch("extract.feedparser.parse")
@patch("extract.requests.get")
def test_extract_feed_requests_with_user_agent_and_timeout(mock_get, mock_parse):
    mock_response = MagicMock()
    mock_response.content = b""
    mock_get.return_value = mock_response
    mock_parse.return_value = MagicMock(entries=[])

    url = "https://example.com/feed"
    extract_feed(url)

    args, kwargs = mock_get.call_args
    assert args[0] == url
    assert "User-Agent" in kwargs["headers"]
    assert kwargs["timeout"] == 10


@patch("extract.feedparser.parse")
@patch("extract.requests.get")
def test_extract_feed_parses_response_content(mock_get, mock_parse):
    mock_response = MagicMock()
    mock_response.content = b"raw feed bytes"
    mock_get.return_value = mock_response
    mock_parse.return_value = MagicMock(entries=[])

    extract_feed("https://example.com/feed")

    mock_parse.assert_called_once_with(b"raw feed bytes")


@patch("extract.feedparser.parse")
@patch("extract.requests.get")
def test_extract_feed_handles_empty_entries(mock_get, mock_parse):
    mock_response = MagicMock()
    mock_response.content = b""
    mock_get.return_value = mock_response
    mock_parse.return_value = MagicMock(entries=[])

    result = extract_feed("https://example.com/feed")

    assert result.entries == []


def test_feed_to_dataframe_returns_dataframe():
    mock_feed = MagicMock()
    mock_feed.entries = [{"title": "Entry 1"}, {"title": "Entry 2"}]

    df = feed_to_dataframe(mock_feed)

    assert not df.empty
    assert list(df.columns) == ["title", "author",
                                "published", "link", "tags", "content"]
    assert len(df) == 2


def test_feed_to_dataframe_tags_joined():
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": "Entry 1", "tags": [{"term": "tag1"}, {"term": "tag2"}]},
        {"title": "Entry 2", "tags": [{"term": "tag3"}]}
    ]

    df = feed_to_dataframe(mock_feed)

    assert df.loc[0, "tags"] == "tag1, tag2"
    assert df.loc[1, "tags"] == "tag3"


def test_feed_to_dataframe_content_correct_format():
    mock_feed = MagicMock()
    mock_feed.entries = [
        {"title": "Entry 1", "summary": "Content, with, commas\nand newlines"},
        {"title": "Entry 2", "summary": "Another content"}
    ]

    df = feed_to_dataframe(mock_feed)

    assert df.loc[0, "content"] == "Content; with; commas and newlines"
    assert df.loc[1, "content"] == "Another content"


@patch("extract.time.sleep")
@patch("extract.Article")
def test_scrape_article_content_returns_content(mock_article_cls, mock_sleep):
    mock_article = MagicMock()
    mock_article.text = "Some   article \n text"
    mock_article_cls.return_value = mock_article

    result = scrape_article_content("https://example.com/article")

    assert result == "Some article text"


def test_clean_html_content_returns_something():
    result = clean_html_content("<p>Hello <b>world</b></p>")

    assert result
