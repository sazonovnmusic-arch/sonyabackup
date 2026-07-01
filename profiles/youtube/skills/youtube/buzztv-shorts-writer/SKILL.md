---
name: buzztv-shorts-writer
description: "Write YouTube Shorts scripts for Buzz TV channel (@Buzz_TV_RU) — Asian culture, Korea/Japan/China facts, dating, food, places, lifestyle. Localize foreign Shorts to Russian."
platforms: [linux, macos, windows]
---

# Buzz TV Shorts Writer

## Channel Overview

**Channel:** Buzz TV (@Buzz_TV_RU, UC50sOtfTWbnxQmILslaWYZw)
**Subscribers:** 43.3K | **Videos:** 297 | **Format:** Shorts + long-form
**Language:** Russian
**Theme:** Asian culture — Korea, Japan, China. Facts, dating tips, food, interesting places, cultural quirks, lifestyle differences.
**Owner:** Nikita (same owner as sostv)

## Content Strategy

Same approach as sostv: find popular foreign Shorts on Asian topics (ANY language), transcribe, translate, adapt to Russian. NOT from scratch — localization of proven content.

### Topics
- Korean/Japanese/Chinese culture
- Dating tips (dating Korean guys, Asian girls, etc.)
- Food and cuisine
- Interesting places and customs
- Cultural quirks and differences from Russia/West
- Lifestyle facts
- "Things you didn't know about [country]"

### Source Priority
1. **Foreign Shorts** (any language) with good views — translate + adapt
2. **Foreign long videos** — extract interesting points
3. **Reddit / forums** — secondary source when YouTube doesn't have enough
4. **Russian Shorts** — last resort, never 1:1

### Franchise/Topic Allowlist
- ✅ Korea (South Korea)
- ✅ Japan
- ✅ China
- ✅ Other Asian countries (Thailand, Vietnam, etc.)
- ❌ No anime content (this is a culture channel, not animation)

## Writing Style

Similar conversational Russian style as sostv, but adapted for this channel:

### Key differences from sostv:
- **No CTA block** — Buzz TV videos don't have mid-text "like/subscribe" blocks
- **No closing question** — not every video ends with a question
- **More informational** — facts and observations, not theories/mysteries
- **Shorter intros** — get straight to the point
- **Tone:** Conversational, informative, slightly entertaining

### Structure
1. **Hook** — "Три безумные вещи в [страна]", "Посмотри это перед тем, как [действие]...", "Все странности [тема]..."
2. **2-3 facts/points** — short, punchy, interesting
3. **Closing** — can be a question or just a natural ending

### Text length
- ~40-60 seconds when spoken
- ~80-150 words
- Match the length of the 4 reference videos (42-59 sec each)

### Language
- Conversational Russian, "ты"
- Simple, accessible
- No complex terms

## Pre-Task Channel Analysis

Same as sostv — ALWAYS check latest videos first:
1. Check latest 4-10 videos on the channel via API
2. Note which topics perform well (the Korea dating video got 23.9K + 1.7K likes — best performer)
3. Don't repeat recent topics
4. Suggest variety — if last 3 were about Korea, try Japan or China

## No-Repetition Rule

Same as sostv — check archive (when available) and channel video titles before producing new scripts. 1 overlap = OK, 2+ = replace.

## Delivery Format

- Send ready-to-record scripts in Telegram
- Only the adapted Russian text
- **Under each text:** link to original video (`Оригинал: https://youtube.com/shorts/VIDEO_ID`)
- Separate multiple texts visually
- Short topic note in brackets before each text: "(Корея — факты)"
- 3-5 texts per batch
- **Multi-channel context:** This channel is served in the SAME daily digest as sostv, but as a SEPARATE section. Send sostv first, then Buzz TV. Never mix the two channels' content in the same section. Use clear headers: `🎬 sostv — Дайджест` and `🌏 Buzz TV — Дайджест`.

## Reference Videos (latest 4)

1. "Три безумные вещи в Южной Корее" — 42 sec, 15.4K views
2. "Посмотри это перед встречей с Японцем" — 46 sec, 1.5K views
3. "Все странности Азиатских девушек" — 53 sec, 1.3K views
4. "Посмотри перед тем, как встречаться с корейцами" — 59 sec, 23.9K views, 1.7K likes (BEST)

## Search Strategy

Use YouTube Data API with these query patterns (in multiple languages):
- "korea facts", "japan facts", "china facts"
- "dating korean", "dating japanese", "asian culture"
- "korean food", "japanese culture", "things about korea"
- "korea vs", "japan vs", "asian countries"
- Try in: English, Spanish, French, German, Portuguese, Korean, Japanese
- Filter by viewCount, target 200K+ views

### Multi-language search is CRITICAL

Do NOT limit to English. Spanish-language Asia content channels get millions of views. Search in Spanish: "cosas sobre corea", "datos sobre japon", "cultura asiatica". Portuguese: "coisas sobre coreia", "fatos sobre japao". Korean: "한국 사실". Japanese: "日本の事実".

### Transcript Fetching — Using Gonzo Proxies (MANDATORY)

**ПРИОРИТЕТ: всегда сначала доставать транскрипт из видео через прокси Gonzo.** Текст из видео уже готовый материал — остаётся только адаптировать под русский. Только если транскрипт получить вообще никак — опираться на название/описание.

YouTube блокирует direct IP (429 Too Many Requests). Решение — прокси Gonzo.

```python
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
import time

# Вариант 1 — US, TTL 6h
proxy_url = "http://GonzoNvv5Rfv_c_us_s_acc69)7(:RqFaYSd6@62.169.20.75:1000"

# Вариант 2 — Finland, TTL 240h (pool)
proxy_url = "http://GonzoNvv5Rfv_c_fi_s_acc142(:RqFaYSd6@pool.gonzoproxy.com:1000"

# Вариант 3 — static
proxy_url = "http://ZmdkDRao:9BH7ZtXCxI4w@45.14.112.25:24295"

proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
ytt = YouTubeTranscriptApi(proxy_config=proxy_config)
transcript = ytt.fetch(video_id, languages=['en', 'es', 'fr', 'de', 'pt', 'ko', 'ja'])
text = " ".join([snippet.text for snippet in transcript])
```

#### Смена IP при блокировке:
- В логине прокси 1 и 2 есть `accXXX` — поменять цифру/букву → IP меняется автоматически
- Пример: `acc69)7(` → `acc70)7(` — новый IP
- Перебирай прокси по порядку. Если один не работает — пробуй следующий или меняй accXXX
- Добавляй 2-3 сек задержки между транскриптами (time.sleep(2))
- Если все прокси не помогают — browser fallback (открыть видео, вытащить субтитры через JS)
- Только если НИЧЕГО не работает — опирайся на название/описание видео

### Pitfalls
- Many Shorts lack transcripts, try 5-10 IDs to get 2-3 working
- Add Korean (ko) and Japanese (ja) to the language fallback chain — this is an Asia-focused channel
- **PACING IS MANDATORY**: Add 3-5 second pauses between transcript fetches. The cron job has a 1.5-hour window — no need to rush. Prevents YouTube IP bans and server overload.
- **If proxy IP stops working**: change `accXXX` in the proxy username to rotate to a new IP.
- **WebshareProxyConfig vs GenericProxyConfig**: Use `GenericProxyConfig(http_url=..., https_url=...)` for Gonzo proxies, NOT `WebshareProxyConfig` (which only works with Webshare's own API).
- **API key security**: `YOUTUBE_API_KEY` in `.env` may display as `***` in terminal. Always read it programmatically with Python. If API returns 400, the key may need re-providing.

## YouTube Analytics API (OAuth — confirmed not working for managers)

YouTube Analytics API does NOT work for manager-level access — only channel owners or CMS/MCN accounts. Tested June 2026 with scopes `yt-analytics.readonly`, `yt-analytics-monetary.readonly`, and `youtube.readonly`. All return 403 Forbidden for channels where the user is manager, not owner. OAuth credentials are stored in `.env` but can only access the user's personal channel, not Buzz TV.

**What IS available via YouTube Data API v3 (API key, no OAuth):**
- ✅ Views, likes, comments per video
- ✅ Subscriber count, total views, video count
- ✅ Upload dates, video durations

**What requires owner OAuth (NOT available):**
- ❌ Audience retention, traffic sources, watch time, demographics, revenue

For full channel analytics, use `scripts/channel_analytics.py` from the sostv-shorts-writer skill (works with any channel ID via `--channel` parameter).

## Cron Execution (Confirmed Working)

**Daily digest cron** runs at 4:30 MSK (1:30 UTC) with pacing:
- 3-5 sec pauses between transcript fetches
- 30 sec pause between sostv and Buzz TV sections
- Max 10 transcripts per channel per session
- Model: glm-5.2 (not Gemini Flash — that's for trend-scouting only)

**Confirmed 21.06.2026:** Cron-агент успешно использовал прокси Gonzo (сменил IP с acc69 на acc70), вытащил 5 транскриптов для Buzz TV из видео с 28M-131M просмотрами. Все тексты основаны на реальных субтитрах.