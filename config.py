import os

# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")  # e.g. "@YourChannel" or "-1001234567890"

# ── Run behaviour ─────────────────────────────────────────
LOOKBACK_MINUTES = 25          # only consider items published within this window
SEND_DELAY_SECONDS = 2         # gap between consecutive immediate/keyword-match sends (flood-limit safety)

# ── Queue (non-matching items) ────────────────────────────
# Items that don't hit ROUTING_KEYWORDS are held here instead of posted
# immediately, then drained a few at a time, spaced out, on every run.
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "queue.json")

# Tunable — how many queued items to drain per run. Spec calls for 4-8;
# starting at the top of that range. Raise this once real per-run volume
# across all 12 sources has been observed (this is the first knob to turn
# if the queue is growing faster than it drains).
QUEUE_DRAIN_MAX = 8

# Spec: "space each post exactly 1 minute apart" while draining the queue.
# NOTE this is separate from SEND_DELAY_SECONDS above (which only applies
# to immediate keyword-match posts within the same run).
QUEUE_DRAIN_INTERVAL_SECONDS = 60

# Spec: drop items that have been sitting in the queue longer than this
# instead of posting them late.
QUEUE_MAX_AGE_HOURS = 8

# ── Keyword routing list — EASY TO EDIT, kept as a flat constant ─────
# Applied identically to every source (no special-casing, including Trump's
# posts). A title/content match here means: post immediately, no queue,
# no pacing, bypasses everything else below.
ROUTING_KEYWORDS = [
    "dies", "breaking", "crash", "war", "resigns", "attack", "emergency",
    "plunge", "surge", "halt", "ban", "hack", "collapse",
]

# ── Direct RSS feeds (category -> list of feed URLs) ──────
# NOTE ON NEW FEED URLS BELOW: added per the 12-source spec. This sandbox
# has no general outbound internet access (only a small allowlist, e.g.
# github.com), so these could NOT be curl-tested before committing them.
# Verify each one resolves and parses (feedparser.parse(url).bozo == False)
# before relying on it in production — swap/fix any that 404 or redirect.
RSS_FEEDS = {
    "GEOPOLITICS": [
        "https://www.aljazeera.com/xml/rss/all.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        # Reuters retired its public RSS feeds years ago (no stable direct
        # feed exists any more) — geopolitics/world coverage from Reuters is
        # instead pulled via the existing GOOGLE_NEWS_QUERIES["GEOPOLITICS"]
        # query below, which already indexes Reuters among other outlets.
    ],
    "TRUMP": [
        "https://trumpstruth.org/feed",  # verified live — returns real RSS/XML
    ],
    "FED_MACRO": [
        "https://www.federalreserve.gov/feeds/press_all.xml",  # verified live
        "https://www.investing.com/rss/central_banks.rss",  # verified live — Central Bank Speeches (covers RBI-adjacent global central bank news, not RBI-specific)
        # RBI itself still has no confirmed public RSS feed for its own press
        # releases — the direct fetch to website.rbi.org.in timed out from
        # here (government site, possibly slow/blocked). Would need a
        # requests+BeautifulSoup scraper (same pattern as
        # fetch_telegram_channel() in sources.py) built against the live
        # page structure. Not wired in yet — flagging as a follow-up.
    ],
    "COMMODITIES": [
        "https://oilprice.com/rss/main",  # verified live (gzip-encoded RSS, confirmed reachable)
        "https://www.investing.com/rss/news_11.rss",  # verified live — Commodities & Futures News
        # Kitco has NO working public RSS — both candidate URLs
        # (kitco.com/rss/KitcoNews.xml and /news/category/*/feed) resolve to
        # the site's Next.js HTML shell, not a feed. Dropped rather than
        # wired in with a URL that 200s but returns HTML.
    ],
    "FOREX": [
        "https://www.investing.com/rss/news_1.rss",  # verified live — Forex News
        # DailyFX's old /feeds/all URL 301-redirects to ig.com's homepage
        # (DailyFX was folded into IG's site) — dead, dropped rather than
        # wired in broken.
    ],
    "CRYPTO": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cointelegraph.com/rss",
        # CoinDesk + CoinTelegraph were already present here before this
        # change (source #8 in the spec is already covered) — no duplicate
        # entries added.
    ],
    "INDIA_MARKETS": [
        "https://www.livemint.com/rss/markets",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/marketreports.xml",  # UNVERIFIABLE — moneycontrol.com is on this fetch tool's own blocklist (compliance rule, unrelated to whether the feed itself works), so this could not be checked from here either way. moneycontrol.com/rss/<section>.xml is the site's real, long-standing RSS URL convention, so this is plausible but not confirmed — verify manually (curl it, or just let the bot run once and check the logs for a parse failure).
    ],
    "IPO": [
        # Chittorgarh has no confirmed RSS — chittorgarh.com/rss/news.xml
        # returned an empty response (likely a dead/incorrect path) and no
        # official feed turned up searching their site. Their IPO news lives
        # at chittorgarh.com/sitemap/ipo-news/34/, which is a plain sitemap
        # page, not a feed — would need a scraper, not wired in yet.
    ],
    "EARNINGS": [
        "https://www.investing.com/rss/news_1062.rss",  # verified live — Earnings Reports and Whispers (global, not Moneycontrol-specific)
        # This is investing.com's real earnings-news feed, used as a working
        # stand-in for source #12. Moneycontrol's own earnings calendar is a
        # structured calendar (one row per company/date), not an article
        # feed — no RSS for it; wiring that in for real needs a scraper
        # against moneycontrol.com/earnings-calendar (same pattern as the
        # Telegram wire scraper), not attempted here since moneycontrol.com
        # is blocked in my fetch tool and I couldn't inspect the live markup.
    ],
    "MACRO_CALENDAR": [
        "https://www.investing.com/rss/news_95.rss",  # verified live — Economic Indicators News
        # This is investing.com's real news-about-indicators feed, used as a
        # working stand-in for source #4. It is NOT the literal economic
        # calendar widget/table (Trading Economics' calendar and Investing's
        # own /economic-calendar/ page are structured data, not RSS) — this
        # feed only carries article-style commentary on indicator releases.
        # A true calendar-row-per-item feed would need Trading Economics'
        # paid API or a scraper against the calendar page.
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
    "TRUMP": "📢",
    "COMMODITIES": "🛢️",
    "FOREX": "💱",
    "IPO": "📈",
    "EARNINGS": "📊",
    "MACRO_CALENDAR": "🗓️",
}

# NOTE: this list is unchanged and still only drives the "JUST IN" prefix /
# display priority in classify.py — it is a superset of ROUTING_KEYWORDS
# above and intentionally kept separate. ROUTING_KEYWORDS (used for the new
# immediate-post-vs-queue decision) is the one the spec asked to keep easy
# to edit; this one is cosmetic/sort-order only and untouched by this change.
BREAKING_KEYWORDS = [
    "strike", "strikes", "attack", "ceasefire", "war", "invade", "invasion",
    "explosion", "missile", "crashes", "plunges", "soars", "surges",
    "falls under", "tumbles", "plummets", "rate cut", "rate hike",
    "resigns", "collapse", "emergency", "banned", "sanctions", "hacked",
    "breach",
]
