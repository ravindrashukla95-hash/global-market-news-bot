import os

# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")  # e.g. "@YourChannel" or "-1001234567890"

# ── Run behaviour ─────────────────────────────────────────
MAX_POSTS_PER_RUN = 8          # cap per run so one flood of news doesn't spam the channel
LOOKBACK_MINUTES = 25          # only consider items published within this window
SEND_DELAY_SECONDS = 2         # gap between consecutive Telegram sends (flood-limit safety)

# ── Direct RSS feeds (category -> list of feed URLs) ──────
RSS_FEEDS = {
    "GEOPOLITICS": [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
    ],
    "CRYPTO": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
    ],
    "INDIA_MARKETS": [
        "https://www.livemint.com/rss/markets",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    ],
}

# ── Public Telegram wire channels (scraped via t.me/s/<channel>, no API key) ──
# Each entry is just a channel username (no @). Categories are auto-detected
# per-post from the text — see _classify_wire_text() in sources.py.
TELEGRAM_WIRE_CHANNELS = [
    "Indiaredboxglobal",  # Redbox Global India — free public mirror of the RedboxWire terminal feed (delayed, partial)
]

# ── Google News search queries (category -> query text) ───
# Encoded + fetched dynamically in sources.py, so special characters here are fine.
GOOGLE_NEWS_QUERIES = {
    "GEOPOLITICS": '(Iran OR Israel OR Russia OR Ukraine OR Taiwan OR China) (strike OR attack OR ceasefire OR war OR sanctions) when:1h',
    "FED_MACRO": 'Federal Reserve OR "interest rate" OR inflation OR CPI when:2h',
    "GLOBAL_MARKETS": 'stock market OR "Wall Street" OR Nasdaq OR S&P500 when:1h',
}

# ── Flag emojis — matched with word boundaries, max 2 flags per headline ─
FLAG_MAP = {
    "iran": "🇮🇷", "israel": "🇮🇱", "russia": "🇷🇺", "ukraine": "🇺🇦",
    "china": "🇨🇳", "taiwan": "🇹🇼", "india": "🇮🇳", "japan": "🇯🇵",
    "uk": "🇬🇧", "britain": "🇬🇧", "europe": "🇪🇺",
    "trump": "🇺🇸", "fed": "🇺🇸", "united states": "🇺🇸",
    "usa": "🇺🇸", "america": "🇺🇸",
}

CATEGORY_EMOJI = {
    "GEOPOLITICS": "🌍",
    "FED_MACRO": "🏦",
    "CRYPTO": "₿",
    "INDIA_MARKETS": "🇮🇳",
    "GLOBAL_MARKETS": "🌐",
}

BREAKING_KEYWORDS = [
    "strike", "strikes", "attack", "ceasefire", "war", "invade", "invasion",
    "explosion", "missile", "crashes", "plunges", "soars", "surges",
    "falls under", "tumbles", "plummets", "rate cut", "rate hike",
    "resigns", "collapse", "emergency", "banned", "sanctions", "hacked",
    "breach",
]
