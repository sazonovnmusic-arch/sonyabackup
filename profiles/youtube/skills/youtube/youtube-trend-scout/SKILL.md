---name: youtube-trend-scout
description: "Find fast-growing Shorts channels on YouTube — channels under 2 months old with high Views/Subs ratios. Trend discovery for new channel ideas."
platforms: [linux, macos, windows]
---

# YouTube Trend Scout

## What This Skill Does

Searches YouTube for **fast-growing Shorts channels** — channels created within the last 2 months that show signs of viral growth (high Views/Subs ratio, multiple successful videos). Used for discovering trending topics and potential new channel ideas for Nikita.

## Criteria for a Trending Channel (STRICT)

1. **Format:** Shorts-only channels (videoDuration=short). Not long-form.
2. **Age:** Created within the last 2 months (60 days from today)
3. **Growth signals:**
   - Subscribers anomalously high for channel age (10K+ in first month)
   - Views/Subs ratio > 5x (viral content outperforming channel size)
   - Multiple videos with 100K+ views (not a single lucky hit)
4. **Topic:** ANY topic. Do not limit to existing channel themes.
5. **Language:** ANY language. Language is NOT a filter criterion.

## Search Methodology

### Step 1: Broad keyword search across languages

Use YouTube Data API v3 (key in `.env` as `YOUTUBE_API_KEY`). Search for trending Shorts sorted by view count, published in last 30 days.

```
search.list(q=<query>, order="viewCount", videoDuration="short",
            publishedAfter=<30 days ago>, maxResults=10)
```

Search queries should span topics AND languages. See `references/search-queries.md` for the full query bank.

### Step 2: Filter videos by views

For each search batch, call `videos.list` with `part="statistics,snippet"` to get view counts. Keep only videos with **100K+ views**.

### Step 3: Check channel age

Collect unique `channelId` values from qualifying videos. Call `channels.list` with `part="snippet,statistics"` in batches of 50. Filter to channels where `publishedAt` (creation date) is within the last 60 days.

### Step 4: Calculate growth metrics

For each young channel:
- **Views/Subs ratio** = totalViews / subscriberCount
- **Videos with 100K+** = count of high-performing videos
- **Country** = channel country (if available)
- Sort by subscriber count descending

### Step 5: Deep-dive top channels

For each qualifying channel, fetch their top 10 videos (by view count) via `search.list(channelId=..., order="viewCount")` + `videos.list` to see what content is performing.

## Pacing — Do NOT Hammer the API

- **3-second delay** between API calls (`time.sleep(3)`)
- Max 20 search queries per session
- Max 10 channel-detail batches per session
- If you hit quota errors (403), stop and report what you have

## Proxy for Browser Fallback

If using browser tools and IP is blocked, use Gonzo proxies:
- `http://GonzoNvv5Rfv_c_us_s_acc69)7(:RqFaYSd6@62.169.20.75:1000`
- `http://GonzoNvv5Rfv_c_fi_s_acc142(:RqFaYSd6@pool.gonzoproxy.com:1000`
- `http://ZmdkDRao:9BH7ZtXCxI4w@45.14.112.25:24295`
- IP change: swap digits in `accXXX` portion of the username

## Report Format

```
🔥 Тренды недели — Быстрорастущие Shorts-каналы

[If nothing found: "В этот раз не нашёл подходящих каналов."]

**N. [Channel Name]**
🔗 https://www.youtube.com/channel/CHANNEL_ID
📅 Создан: [date]
👥 Подписчиков: [number]
📊 Просмотров на топовом видео: [number]
📈 Views/Subs ratio: [number]x
🎬 Видео на канале: [count], из них с 100K+ просмотрами: [count]
🌐 Язык: [language]
🏷 Тематика: [description]
📝 Почему это тренд: [1-2 sentences]
💡 Идея для локализации: [how to adapt to Russian — brief]
```

Rules:
- Only REAL channels found via API. Never fabricate.
- If 0 found — say so honestly.
- 1-5 channels per report. More than 5 is unnecessary.
- Include a summary table of trending topics at the end.

## Cron Configuration

This skill runs weekly via cron job (Mondays at 8:30 MSK / 5:30 UTC).
Model: `gemini-3-flash-preview` (light model — mechanical work, no heavy reasoning needed).

## Reference Files

- `references/search-queries.md` — Full bank of search queries across 12+ languages and 20+ topic categories, including proven trending topics from test runs
- `references/test-run-2026-06-20.md` — First successful test run results: 9 channels found, trending topics identified (psychology/aura, DIY garden, shock facts, What-If, quizzes, movie facts), technique notes
- `scripts/trend_scout.py` — Reusable Python script for automated trend scouting