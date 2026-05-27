"""RSS news scraper with ticker tagging + VADER sentiment.

Fetches all feeds in `settings.news_feeds`, dedups by URL hash, extracts
mentioned tickers via simple regex aliases, scores sentiment with VADER,
and upserts into the `news` table. Rows older than `news_ttl_days` are
purged at the end of each run.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import feedparser
import httpx
from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from ..config import settings
from .db import News, session_scope

log = logging.getLogger(__name__)


# --- Ticker aliases ----------------------------------------------------------
# Each ticker maps to a list of patterns. Short or ambiguous tickers use
# explicit word-boundary regex (e.g. MU, CRM, TXN, NOW).
TICKER_ALIASES: dict[str, list[str]] = {
    "AAPL": ["AAPL", "Apple"],
    "MSFT": ["MSFT", "Microsoft"],
    "NVDA": ["NVDA", "Nvidia"],
    "GOOGL": ["GOOGL", "GOOG", "Google", "Alphabet"],
    "META": ["META", "Meta Platforms", "Facebook"],
    "AMZN": ["AMZN", "Amazon"],
    "TSLA": ["TSLA", "Tesla"],
    "AVGO": ["AVGO", "Broadcom"],
    "AMD": ["AMD", "Advanced Micro Devices"],
    "INTC": ["INTC", "Intel"],
    "QCOM": ["QCOM", "Qualcomm"],
    "MU": [r"\bMU\b", "Micron"],
    "ORCL": ["ORCL", "Oracle"],
    "CRM": [r"\bCRM\b", "Salesforce"],
    "ADBE": ["ADBE", "Adobe"],
    "NFLX": ["NFLX", "Netflix"],
    "PYPL": ["PYPL", "PayPal"],
    "CSCO": ["CSCO", "Cisco"],
    "TXN": [r"\bTXN\b", "Texas Instruments"],
    "NOW": [r"\bNOW\b", "ServiceNow"],
}


def _compile_patterns() -> dict[str, list[re.Pattern[str]]]:
    """Pre-compile aliases into case-insensitive word-boundary regexes."""
    compiled: dict[str, list[re.Pattern[str]]] = {}
    for ticker, patterns in TICKER_ALIASES.items():
        compiled[ticker] = []
        for p in patterns:
            # If the pattern already contains \b, use as-is. Otherwise wrap.
            rx = p if r"\b" in p else rf"\b{re.escape(p)}\b"
            compiled[ticker].append(re.compile(rx, re.IGNORECASE))
    return compiled


_COMPILED_PATTERNS = _compile_patterns()

_ANALYZER = SentimentIntensityAnalyzer()


# --- Public helpers (also used by tests) -------------------------------------
def tag_tickers(text: str) -> list[str]:
    """Return list of tickers mentioned in `text` (uniqued, ordered by
    ticker symbol in `settings.tickers` order)."""
    if not text:
        return []
    hits: list[str] = []
    for ticker in settings.tickers:
        patterns = _COMPILED_PATTERNS.get(ticker)
        if not patterns:
            continue
        if any(rx.search(text) for rx in patterns):
            hits.append(ticker)
    return hits


def score_sentiment(text: str) -> tuple[str, float]:
    """Score `text` with VADER. Returns (label, compound_score)."""
    if not text:
        return ("neu", 0.0)
    scores = _ANALYZER.polarity_scores(text)
    compound = float(scores["compound"])
    if compound >= 0.05:
        label = "pos"
    elif compound <= -0.05:
        label = "neg"
    else:
        label = "neu"
    return (label, compound)


# --- Fetching ----------------------------------------------------------------
async def _fetch_feed(client: httpx.AsyncClient, url: str) -> tuple[str, str | None]:
    """Fetch one feed URL. Returns (url, body_text-or-None)."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=15.0)
        resp.raise_for_status()
        return (url, resp.text)
    except Exception as e:
        log.warning("news feed fetch failed for %s: %s", url, e)
        return (url, None)


async def _fetch_all_feeds(urls: list[str]) -> list[tuple[str, str | None]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; SwingTradeRadar/0.1; "
            "+https://github.com/swing-trade-radar)"
        )
    }
    async with httpx.AsyncClient(headers=headers) as client:
        return await asyncio.gather(*(_fetch_feed(client, u) for u in urls))


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def _entry_published(entry: Any) -> datetime:
    """Best-effort datetime parse from a feedparser entry."""
    for attr in ("published_parsed", "updated_parsed"):
        tm = getattr(entry, attr, None) or (
            entry.get(attr) if hasattr(entry, "get") else None
        )
        if tm:
            try:
                return datetime(*tm[:6])
            except Exception:
                continue
    return datetime.utcnow()


def _source_from_url(url: str) -> str:
    try:
        host = httpx.URL(url).host or ""
        host = host.removeprefix("www.")
        return host or "unknown"
    except Exception:
        return "unknown"


def _parse_and_collect(body: str, feed_url: str) -> list[dict[str, Any]]:
    parsed = feedparser.parse(body)
    source = _source_from_url(feed_url)
    out: list[dict[str, Any]] = []
    for entry in parsed.entries or []:
        link = getattr(entry, "link", "") or ""
        title = (getattr(entry, "title", "") or "").strip()
        summary = (getattr(entry, "summary", "") or "").strip()
        if not link or not title:
            continue
        published = _entry_published(entry)
        text = f"{title} {summary}".strip()
        tickers = tag_tickers(text)
        label, score = score_sentiment(text)
        out.append(
            dict(
                url_hash=_hash_url(link),
                title=title[:1024],
                summary=summary[:4096],
                source=source[:128],
                url=link[:2048],
                published_at=published,
                tickers=tickers,
                sentiment=label,
                sentiment_score=score,
            )
        )
    return out


def scrape_all() -> dict[str, int]:
    """Scrape all configured RSS feeds. Returns counts dict."""
    urls = list(settings.news_feeds)
    if not urls:
        return {"fetched": 0, "new": 0, "purged": 0}

    try:
        results = asyncio.run(_fetch_all_feeds(urls))
    except RuntimeError:
        # Likely already inside a running loop — fall back to sync httpx.
        results = []
        with httpx.Client(
            headers={"User-Agent": "SwingTradeRadar/0.1"}, timeout=15.0
        ) as client:
            for u in urls:
                try:
                    r = client.get(u, follow_redirects=True)
                    r.raise_for_status()
                    results.append((u, r.text))
                except Exception as e:
                    log.warning("sync feed fetch failed for %s: %s", u, e)
                    results.append((u, None))

    # Parse + dedup by url_hash (within this run).
    items_by_hash: dict[str, dict[str, Any]] = {}
    for feed_url, body in results:
        if not body:
            continue
        for item in _parse_and_collect(body, feed_url):
            items_by_hash.setdefault(item["url_hash"], item)

    fetched = len(items_by_hash)
    new_count = 0

    if items_by_hash:
        rows = list(items_by_hash.values())
        with session_scope() as s:
            existing = set(
                s.execute(
                    select(News.url_hash).where(News.url_hash.in_(list(items_by_hash.keys())))
                ).scalars().all()
            )
            new_count = len([r for r in rows if r["url_hash"] not in existing])
            stmt = sqlite_insert(News).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=["url_hash"])
            s.execute(stmt)

    # Purge old.
    purged = 0
    cutoff = datetime.utcnow() - timedelta(days=settings.news_ttl_days)
    with session_scope() as s:
        res = s.execute(delete(News).where(News.published_at < cutoff))
        purged = int(res.rowcount or 0)

    summary = {"fetched": fetched, "new": new_count, "purged": purged}
    log.info("news scrape: %s", summary)
    return summary


# --- Read API ---------------------------------------------------------------
def latest_news(ticker: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Return latest news rows, newest first. Optionally filter by ticker."""
    with session_scope() as s:
        q = select(News).order_by(News.published_at.desc())
        rows = s.execute(q.limit(max(limit * 4, limit))).scalars().all()

    out: list[dict[str, Any]] = []
    t = ticker.upper() if ticker else None
    for r in rows:
        tickers = list(r.tickers or [])
        if t and t not in tickers:
            continue
        out.append(
            dict(
                id=r.id,
                title=r.title,
                summary=r.summary,
                source=r.source,
                url=r.url,
                published_at=r.published_at.isoformat() if r.published_at else None,
                tickers=tickers,
                sentiment=r.sentiment,
                sentiment_score=r.sentiment_score,
            )
        )
        if len(out) >= limit:
            break
    return out
