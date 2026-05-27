"""Unit tests for news_scraper: ticker tagging + VADER sentiment.

Pure-function tests; no network and no DB writes.
"""

from __future__ import annotations

from swing_trader.data.news_scraper import score_sentiment, tag_tickers


# --- tag_tickers -------------------------------------------------------------
def test_tag_tickers_apple_by_name():
    assert tag_tickers("Apple beats Q1 expectations") == ["AAPL"]


def test_tag_tickers_apple_by_symbol():
    assert tag_tickers("AAPL surges on strong iPhone sales") == ["AAPL"]


def test_tag_tickers_multiple():
    hits = tag_tickers("Tesla and Nvidia surge after AI announcement")
    assert set(hits) == {"TSLA", "NVDA"}


def test_tag_tickers_alphabet_alias():
    # Both GOOGL aliases (Google, Alphabet, GOOG) should map to GOOGL.
    assert tag_tickers("Alphabet posts record ad revenue") == ["GOOGL"]
    assert tag_tickers("Google Cloud grows 30%") == ["GOOGL"]


def test_tag_tickers_short_symbol_needs_word_boundary():
    # "MU" should match standalone but not inside another word.
    assert tag_tickers("MU reports strong memory demand") == ["MU"]
    # Should NOT match "MUSIC" or "AMUSEMENT".
    assert tag_tickers("AMUSEMENT parks booming this summer") == []


def test_tag_tickers_empty():
    assert tag_tickers("Random unrelated news about pandas") == []
    assert tag_tickers("") == []


def test_tag_tickers_case_insensitive():
    assert tag_tickers("apple AND microsoft both rallied") == ["AAPL", "MSFT"]


def test_tag_tickers_returns_unique():
    # Multiple mentions should not duplicate.
    hits = tag_tickers("Apple Apple AAPL iPhone Apple")
    assert hits == ["AAPL"]


# --- score_sentiment ---------------------------------------------------------
def test_sentiment_positive():
    label, score = score_sentiment(
        "Apple surges to record highs on stellar earnings, analysts excited"
    )
    assert label == "pos"
    assert score >= 0.05


def test_sentiment_negative():
    label, score = score_sentiment(
        "Tesla plunges on disastrous quarter, awful guidance, layoffs feared"
    )
    assert label == "neg"
    assert score <= -0.05


def test_sentiment_neutral():
    label, score = score_sentiment("The company filed its 10-K with the SEC today")
    assert label == "neu"
    assert -0.05 < score < 0.05


def test_sentiment_empty_string():
    label, score = score_sentiment("")
    assert label == "neu"
    assert score == 0.0
