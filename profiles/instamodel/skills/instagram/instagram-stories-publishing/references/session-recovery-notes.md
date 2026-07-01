# Instagram Stories Publishing — Session Notes

## Token Exchange Reality

- The actual app issuing tokens is **DirectSonya** (app_id: 1841927200521952), NOT SonyaHermes.
- `fb_exchange_token` endpoint rejected Python `urllib` requests with generic "Invalid request" / 400 errors.
- **Solution: use `curl` directly** for token exchange.
- Current token (as of 2026-06-30) works despite `expires_at` showing past time — Graph API may grant a grace period or auto-refresh on use.

## Cronjob Recovery Pattern

When cronjobs are deleted/lost:

1. Check `cronjob list` — confirm empty
2. Locate existing script: `find /root/.hermes/scripts/ -name "*publish*story*"`
3. Recreate directories: `mkdir -p stories_queue/ stories_published/`
4. Restore token from user or file backup
5. Recreate cronjob with `cronjob create`
6. The `publish_story.py` script is self-contained — only needs:
   - Token file at `~/.hermes/profiles/instamodel/.page_token.txt`
   - `cloudflared` binary at `/tmp/cloudflared`
   - Photos in `stories_queue/`

## Posting Schedule for Kira

- **Timezone:** PT (Pacific / Los Angeles)
- **Frequency:** 3 Stories/day
- **Times:** 9:00, 15:00, 21:00 PT
- **Cron UTC:** `0 16,22,4 * * *`
- **Text captions:** user will configure separately; currently images-only

## App IDs

| App | ID | Status |
|---|---|---|
| DirectSonya | 1841927200521952 | ✅ Active, issues tokens |
| SonyaHermes | 908058175688398 | ❌ Old/deprecated, exchange fails |

## Queue Protocol

User drops batches of photos → agent copies to `stories_queue/` → cron picks one per tick → publishes via Graph API → moves to `stories_published/`
