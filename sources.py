import urllib.parse
from datetime import datetime, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS, GOOGLE_NEWS_QUERIES, TELEGRAM_WIRE_CHANNELS

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArthavidhiNewsBot/1.0)"}

# Lightweight keyword buckets to route a wire post into the same categories
# used elsewhere (RSS_FEEDS / GOOGLE_NEWS_QUERIES), so flags/emojis stay
# consistent no matter which source the item came from.
_WIRE_CATEGORY_KEYWORDS = {
    "FED_MACRO": ["fed", "federal reserve", "rate", "cpi", "inflation", "yield", "treasury", "fomc", "powell"],
    "GEOPOLITICS": ["iran", "israel", "russia", "ukraine", "china", "taiwan", "pakistan", "war", "strike",
                    "sanctions", "attack", "ceasefire", "missile"],
    "INDIA_MARKETS": ["india", "nifty", "sensex", "rbi", "nse", "bse", "rupee"],
    "CRYPTO": ["bitcoin", "btc", "ethereum", "eth", "crypto"],
}


def _classify_wire_text(text, default="GLOBAL_MARKETS"):
    text_lower = text.lower()
    for category, keywords in _WIRE_CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return default


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


def _parse_telegram_datetime(time_tag):
    if not time_tag or not time_tag.get("datetime"):
        return None
    try:
        dt = datetime.fromisoformat(time_tag["datetime"])
        return dt.astimezone(timezone.utc).timetuple()
    except Exception:
        return None


# Posts containing any of these are dropped entirely — either self-promo for
# the source channel (app installs, subscribe/trial pitches) or a mention of
# its own brand name. We never want the source's name or a link back to it
# reaching our subscribers, so anything that even mentions it is discarded
# rather than edited (safer than trying to surgically strip a brand name out
# of a sentence).
_WIRE_EXCLUDE_KEYWORDS = [
    "redbox", "play store", "app store", "free trial", "download now",
    "subscribe", "apk", "signup", "sign up",
]


def _is_wire_post_excluded(title):
    title_lower = title.lower()
    return any(kw in title_lower for kw in _WIRE_EXCLUDE_KEYWORDS)


def fetch_telegram_channel(channel, limit=30):
    """Scrape a public Telegram channel's read-only preview page (t.me/s/<channel>)
    for its plain-text market-wire posts. No login/API key needed — this is
    the same page Telegram serves to search engines and logged-out visitors.

    Deliberately anonymized on the way out: no source name and no link back
    to the origin channel are attached to any item, so our own subscribers
    have no way to find and follow the upstream channel instead of ours.
    Any post that mentions the source's own brand or is self-promotional
    (app download, subscribe/trial pitches, etc.) is dropped outright.
    """
    url = f"https://t.me/s/{channel}"
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for msg in soup.select("div.tgme_widget_message")[-limit:]:
            text_div = msg.select_one("div.tgme_widget_message_text")
            if not text_div:
                continue  # skip photo/file-only posts with no caption
            title = text_div.get_text(" ", strip=True)
            if not title or _is_wire_post_excluded(title):
                continue
            items.append({
                "title": title,
                "link": "",  # intentionally no link back to the source channel
                "published": _parse_telegram_datetime(msg.select_one("time")),
                "category": _classify_wire_text(title),
                "source": "wire",  # internal only — never rendered in the posted message
            })
    except Exception as e:
        print(f"[sources] failed to fetch telegram channel {channel}: {e}")
    return items


def fetch_telegram_sources():
    """Fetch every public Telegram wire channel defined in TELEGRAM_WIRE_CHANNELS."""
    all_items = []
    for channel in TELEGRAM_WIRE_CHANNELS:
        all_items.extend(fetch_telegram_channel(channel))
    return all_items


def fetch_all_sources():
    items = fetch_rss_sources() + fetch_google_news_sources() + fetch_telegram_sources()
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
