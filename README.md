# Global Market News Bot

Free, 24x7 breaking-news channel for markets — geopolitics, Fed/macro, crypto,
India markets, and global markets — in one Telegram feed, styled like a
"JUST IN:" wire service (LMWM News format).

## Cost: ₹0
- Telegram Bot API — free
- RSS / Google News / Binance public endpoints — free
- GitHub Actions — free & unlimited minutes on a **public** repo

## One-time setup

1. **Create the bot**: message [@BotFather](https://t.me/BotFather) →
   `/newbot` → save the token.
2. **Create the channel**: make it public, add the bot as admin with
   "Post Messages" permission.
3. **Get the channel ID**: easiest is to use `@username` (e.g. `@YourChannel`)
   directly as `TELEGRAM_CHANNEL_ID`.
4. **Add repo secrets** (Settings → Secrets and variables → Actions):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHANNEL_ID`
5. **Keep the repo public** so Actions minutes stay unlimited. No secrets
   ever live in code — only in repo secrets.
6. **Enable Discussion** on the channel (Telegram channel settings →
   Discussion → link a group) to get the "Leave a Comment" thread like LMWM.
7. **Enable reactions** (channel settings → Reactions) — these fill up
   organically from real subscribers reacting; the bot doesn't fake them,
   same with view counts, which Telegram tracks automatically per post.
8. Push this repo, then trigger the workflow once manually
   (Actions tab → Global Market News Bot → Run workflow) to confirm it posts.

## Tuning
- `config.py` → add/remove RSS feeds, edit flag emojis, edit
  `BREAKING_KEYWORDS` for what counts as "JUST IN" vs "Update".
- `MAX_POSTS_PER_RUN` and the cron interval control posting cadence —
  keep them balanced so you don't hit Telegram's flood limits.
- `TELEGRAM_WIRE_CHANNELS` in `config.py` → add more public Telegram
  channel usernames (no `@`) to pull in as wire sources. Each one is
  scraped via its read-only `t.me/s/<channel>` preview page — no login
  or API key needed. Currently includes `Indiaredboxglobal`, a free
  public mirror of the RedboxWire market-news terminal feed.
- Slot your existing BSE/NSE corporate-announcement scraper into
  `sources.fetch_all_sources()` to fold India corp-action alerts into
  this same public feed instead of running a second bot.

## Known limitations to plan around
- Google News RSS and Binance public endpoints can rate-limit or change
  format without notice — check Actions run logs periodically.
- GitHub's scheduled cron can lag a few minutes during platform load —
  fine for a news feed, not for sub-minute latency needs.
- Chart generation currently covers BTC only; extend `charts.py` with
  `yfinance` for equity/index charts (e.g. Nifty, SPX) the same way.
- The Telegram wire scraper (`fetch_telegram_channel` in `sources.py`)
  reads Telegram's public HTML preview page, not an official API —
  it's the same technique RSS-bridge tools use, but Telegram could
  change that page's markup at any time, which would silently stop
  that source (everything else keeps working; check logs for
  `failed to fetch telegram channel`). The `Indiaredboxglobal` mirror
  is also explicitly a **delayed, partial** feed — full real-time
  coverage requires Redbox's paid terminal (redboxglobal.com).
