import re
import time

from config import (
    FLAG_MAP, CATEGORY_EMOJI, BREAKING_KEYWORDS, ROUTING_KEYWORDS,
    LOOKBACK_MINUTES,
)


def extract_flags(title):
    """Word-boundary match so short codes like 'uk' don't fire inside 'Ukraine' etc."""
    title_lower = title.lower()
    found = []
    for keyword, flag in FLAG_MAP.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, title_lower) and flag not in found:
            found.append(flag)
        if len(found) == 2:
            break
    return "".join(found)


def is_breaking(title):
    """Cosmetic only — drives the 'JUST IN' prefix / display priority.
    Deliberately kept separate from is_routing_match()/ROUTING_KEYWORDS
    below, which is the new immediate-post-vs-queue routing decision."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in BREAKING_KEYWORDS)


def is_routing_match(item):
    """The spec's keyword check: title/content match -> post immediately,
    bypassing the queue entirely. Applied identically to every source
    (no special-casing by source, including Trump's posts)."""
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    return any(kw in text for kw in ROUTING_KEYWORDS)


def is_recent(published_epoch):
    if not published_epoch:
        return True  # some feeds omit dates — don't discard, just skip the age check
    age_minutes = (time.time() - published_epoch) / 60
    return age_minutes <= LOOKBACK_MINUTES


def enrich(item):
    item["flags"] = extract_flags(item["title"])
    item["breaking"] = is_breaking(item["title"])
    item["category_emoji"] = CATEGORY_EMOJI.get(item["category"], "📰")
    item["priority"] = 2 if item["breaking"] else 1
    item["routing_match"] = is_routing_match(item)
    return item


def process_items(raw_items):
    fresh = [i for i in raw_items if is_recent(i.get("published"))]
    enriched = [enrich(i) for i in fresh]
    enriched.sort(key=lambda i: i["priority"], reverse=True)
    return enriched
