# Telegram Channel Monitoring — Limitations & Workarounds

## Global Search: Not Viable

| Method | Status | Notes |
|--------|--------|-------|
| `tgstat.ru` | BLOCKED | Cloudflare CAPTCHA, bot detection |
| Google `site:t.me` | BLOCKED | IP ban from Google |
| Yandex `site:t.me` | BLOCKED | SmartCaptcha |
| Telegram API search | BLOCKED | No global public search endpoint |
| Direct `t.me/s/CHANNEL` | WORKS | Only for known channel names |

## Viable Approach: Known Channel List

The only working path is user-provided channel list + direct monitoring.

### URL Format
```
https://t.me/s/CHANNEL_NAME
```

### Example Channels (arb/media buying niche)
These were tested and found either private or abandoned:
- `@zarabotok_tg` — abandoned, 14 subscribers, last post 2023
- `@affiliate_marketing_ru` — 10 subscribers, abandoned
- `@cpa_ru` — private
- `@ArbitrageTraffic` — private

### Key Finding
**Quality channels are private or invite-only.** The user must:
1. Search Telegram manually for active channels (via in-app search)
2. Collect public channel URLs (`t.me/s/CHANNEL` or `t.me/CHANNEL`)
3. Provide the list to the agent for monitoring

### Monitoring Workflow
Once channels are known:
1. Navigate to `https://t.me/s/CHANNEL_NAME`
2. Extract posts via DOM parsing (posts are in `.tgme_widget_message`)
3. Filter by keywords: `кейс`, `залив`, `профит`, `связка`, `аккаунты`, `фарм`, `банк`, `слив`, `байер`, `TikTok`, `Facebook`
4. Compile new posts and deliver to user

### Keywords by Niche
| Niche | Keywords |
|-------|----------|
| Media buying arbitrage | `кейс`, `залив`, `профит`, `связка`, `ROI`, `CTR` |
| Account farming | `аккаунты`, `фарм`, `рег`, `банк`, `вериф` |
| Tools & infra | `антидетект`, `прокси`, `Keitaro`, `постбэк` |
| Team/jobs | `ищем байера`, `вакансия`, `remote`, `удалёнка` |
| New directions | `TikTok`, `Facebook`, `Google`, `Telegram Ads` |

## Pitfalls
- `t.me/s/CHANNEL` only shows last ~20-50 posts, not full history
- Post text is often truncated; need to click individual posts for full content
- Rate limiting: Telegram Web may throttle rapid navigation between channels
- Private channels are inaccessible without invite link
