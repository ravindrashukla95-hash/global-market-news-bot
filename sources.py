import urllib.parse

import feedparser
import requests

from config import RSS_FEEDS, GOOGLE_NEWS_QUERIES

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArthavidhiNewsBot/1.0)"}


def _parse_feed(url, category):
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "published": entry.get("published_parsed") or entry.get("updated_parsed"),
                "category": category,
                "source": feed.feed.get("title", url),
            })
    except Exception as e:
        print(f"[sources] failed to parse {url}: {e}")
    return items


def fetch_rss_sources():
    """Fetch every direct RSS feed defined in RSS_FEEDS."""
    all_items = []
    for category, feeds in RSS_FEEDS.items():
        for url in feeds:
            all_items.extend(_parse_feed(url, category))
    return all_items


def fetch_google_news_sources():
    """Fetch Google News RSS search results for each configured query."""
    all_items = []
    for category, query in GOOGLE_NEWS_QUERIES.items():
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        all_items.extend(_parse_feed(url, category))
    return all_items


def fetch_all_sources():
    items = fetch_rss_sources() + fetch_google_news_sources()
    # NOTE: plug your existing NSE/BSE corporate-announcement scraper in here,
    # tagging each item with category="INDIA_MARKETS", to fold it into this
    # same public feed instead of running a second, separate bot.
    return items


def fetch_crypto_move(symbol="BTCUSDT"):
    """24h % move via Binance public API — used to decide if a chart is worth attaching."""
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": symbol}, headers=HEADERS, timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return float(data.get("priceChangePercent", 0))
    except Exception as e:
        print(f"[sources] crypto move check failed: {e}")
        return 0.0
