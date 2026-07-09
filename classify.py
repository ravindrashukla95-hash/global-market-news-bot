import re
import time
import calendar

from config import FLAG_MAP, CATEGORY_EMOJI, BREAKING_KEYWORDS, LOOKBACK_MINUTES


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
    title_lower = title.lower()
    return any(kw in title_lower for kw in BREAKING_KEYWORDS)


def is_recent(published_struct):
    if not published_struct:
        return True  # some feeds omit dates — don't discard, just skip the age check
    published_ts = calendar.timegm(published_struct)
    age_minutes = (time.time() - published_ts) / 60
    return age_minutes <= LOOKBACK_MINUTES


def enrich(item):
    item["flags"] = extract_flags(item["title"])
    item["breaking"] = is_breaking(item["title"])
    item["category_emoji"] = CATEGORY_EMOJI.get(item["category"], "📰")
    item["priority"] = 2 if item["breaking"] else 1
    return item


def process_items(raw_items):
    fresh = [i for i in raw_items if is_recent(i.get("published"))]
    enriched = [enrich(i) for i in fresh]
    enriched.sort(key=lambda i: i["priority"], reverse=True)
    return enriched
