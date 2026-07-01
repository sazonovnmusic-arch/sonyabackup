# YouTube Trend-Scouting Recipe

## Goal
Find fast-growing Shorts channels (<2 months old) with anomalous view/subscriber ratios across ANY language and topic.

## API Workflow

### Step 1: Broad search (YouTube Data API v3)

Search with `order=viewCount`, `videoDuration=short`, `publishedAfter` = 30 days ago.

Multi-language queries (rotate through these — each returns different results):

| Language | Sample queries |
|----------|---------------|
| EN | "amazing facts you didn't know shorts", "psychology tricks shorts", "life hacks shorts", "scary facts shorts", "top 5 things shorts", "hidden details shorts", "unsolved mysteries shorts" |
| ES | "datos curiosos shorts", "curiosidades shorts", "secretos shorts" |
| PT | "curiosidades shorts", "fatos shorts" |
| HI | "rochak tathya shorts", "मजेदार तथ्य" |
| AR | "حقائق shorts", "معلومات غريبة shorts" |
| KO | "흥미로운 사실", "한국 사실" |
| JA | "面白い事実", "知らなかった事実" |

Each search costs 100 API quota units. 10K/day budget = ~100 searches.

### Step 2: Get video stats

For each search result, batch-fetch `videos.list` with `part=statistics,snippet` (1 unit per video, up to 50 IDs per call).

Filter: `viewCount >= 100000` (100K+ views).

### Step 3: Get channel details

Collect unique `channelId` values. Batch-fetch `channels.list` with `part=snippet,statistics` (1 unit per channel, up to 50 per call).

Filter criteria (ALL must pass):
- `publishedAt` < 60 days ago (channel younger than 2 months)
- `subscriberCount` > 5,000 (real growth, not a dead channel)
- `viewCount / subscriberCount > 5x` (viral content, not just loyal subs)
- `videoCount >= 5` (not a one-hit wonder — multiple successful videos)

**Note on videoCount:** Very new channels (10 days old) may have only 8-11 videos but still be genuine trends. If subscriberCount and views are high, videoCount >= 5 is sufficient. Don't require 20+ videos.

### Step 4: Verify with video stats

For each young channel, fetch its top videos (`search.list` with `channelId`, `order=viewCount`, `maxResults=10`). Then `videos.list` for stats.

Check: at least 2-3 videos with 100K+ views = genuine trend, not a fluke.

### Step 5: Report format

```
🔥 Channel Name
🔗 https://www.youtube.com/channel/UC...
📅 Created: YYYY-MM-DD (N days ago)
👥 Subs: X | 📊 Views: Y | 📈 Views/Subs: Zx
🎬 Videos: N (M with 100K+ views)
🌐 Language: [detected]
🏷 Topic: [brief description]
📝 Why trending: [1-2 sentences]
💡 Localization idea: [how to adapt to RU audience]
```

## Pacing

- 3-5 second pauses between API calls to avoid rate limiting
- Max ~20 search queries per session
- Batch video/channel stats (50 IDs per call) to save quota
- Total quota per session: ~2000-3000 units (well within 10K limit)

## Pitfalls

- **API key masked in terminal**: `YOUTUBE_API_KEY` shows as `***` in terminal output. Always read with Python `open()` not `grep`.
- **videoDuration=short filter**: returns Shorts AND short videos under 4 min. To confirm it's a Shorts channel, check that most video durations are PT60S or less.
- **Hindi/Arabic/CJK queries**: YouTube search handles Unicode queries fine. Don't romanize — use native script.
- **Channel age vs video age**: A channel created in 2020 but only posting in the last month doesn't qualify. Check `channel.snippet.publishedAt`, not video dates.
- **Deduplicate**: The same channel appears across multiple searches. Dedupe by channelId before fetching channel details.
- **Views/Subs ratio anomalies**: Ratios above 100x are common for very new channels (few subs, one viral video). The 5x threshold filters out channels that are just old and established.

## Confirmed Results (Test Run — 21 June 2026)

A test run with 12 English-language queries + 8 multilingual queries found 9 channels younger than 2 months. Key findings:

| Channel | Created | Subs | Views | Ratio | Topic | Language |
|---|---|---|---|---|---|---|
| Create & Grow DIY | Apr 27 | 134K | 84.6M | 632x | Garden/DIY hacks | EN (US) |
| FactswithMighty | May 17 | 133K | 32M | 241x | Facts/records | EN (IN) |
| Silent Mind | May 15 | 65.5K | 8.5M | 130x | Psychology/aura | EN (IN) |
| Facto Era | May 17 | 16.2K | 7.1M | 441x | Facts/India | EN (IN) |
| RandomFactsExplained | May 15 | 15.8K | 8.2M | 520x | What-If scenarios | EN (FI) |
| Quiz Aram | May 22 | 15.7K | 1.2M | 79x | Quizzes | EN (US) |
| CineVix | Apr 22 | 9K | 8.7M | 960x | Cinema facts | EN (IN) |

**Top trending themes identified:**
1. **Psychology / "aura" / respect tips for students** — biggest current trend (Silent Mind, Shan 7)
2. **DIY / garden life hacks** — visual, language-agnostic, massive views
3. **Shocking facts / records** — evergreen, works in any language
4. **What-If scenarios** — "Can you drain the ocean?", "What if 800 IQ?"
5. **Interactive quizzes** — "Guess the country by flag"

**API quota used:** ~2200 units (well within 10K limit).