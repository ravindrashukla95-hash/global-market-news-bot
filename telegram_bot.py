import time
import requests

from config import BOT_TOKEN, CHANNEL_ID, SEND_DELAY_SECONDS

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def format_caption(item):
    flags = item.get("flags", "")
    emoji = item.get("category_emoji", "📰")
    prefix = "JUST IN" if item.get("breaking") else "Update"
    text = f"<b>{prefix}:</b> {emoji}{flags} {item['title']}"
    if item.get("link"):
        text += f'\n\n<a href="{item["link"]}">Read more</a>'
    return text


def send_text(item):
    payload = {
        "chat_id": CHANNEL_ID,
        "text": format_caption(item),
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    r = requests.post(f"{API_BASE}/sendMessage", data=payload, timeout=15)
    if not r.ok:
        print(f"[telegram] sendMessage failed: {r.text}")
    return r.ok


def send_photo(item, photo_path):
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {
            "chat_id": CHANNEL_ID,
            "caption": format_caption(item),
            "parse_mode": "HTML",
        }
        r = requests.post(f"{API_BASE}/sendPhoto", data=data, files=files, timeout=30)
    if not r.ok:
        print(f"[telegram] sendPhoto failed: {r.text}")
    return r.ok


def post_item(item, photo_path=None):
    ok = send_photo(item, photo_path) if photo_path else send_text(item)
    time.sleep(SEND_DELAY_SECONDS)
    return ok
