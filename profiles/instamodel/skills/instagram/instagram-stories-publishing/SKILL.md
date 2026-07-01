---
name: instagram-stories-publishing
description: Publish Instagram Stories via Facebook Graph API for @kiraliluna. Covers token management, queue-based publishing, cloudflared tunneling, and scheduling.
triggers:
  - User asks to publish Instagram Stories
  - User mentions auto-posting stories for Kira
  - Need to restore or recreate Instagram Stories cronjob
  - Token expired / Graph API error for stories
  - User asks how to get Instagram API token
  - User says cronjob is missing / deleted / needs recovery
  - Need to exchange short-lived token for long-lived token
---

# Instagram Stories Publishing via Graph API

## Overview

This skill governs automated publishing of Instagram Stories for the account **@kiraliluna** (Kira Liluna). It uses the official Facebook Graph API (`instagram_content_publish`) — the only reliable, non-banning method.

## Account Details (stable)

| Parameter | Value |
|---|---|
| Instagram handle | `@kiraliluna` |
| Account type | Creator |
| Instagram Account ID | `17841463208388373` |
| Facebook App (token issuer) | `DirectSonya` (app_id: `1841927200521952`) |
| Facebook Page | `Kirakira luna` |
| API version | `v18.0` |
| Publishing script | `~/.hermes/scripts/publish_story.py` |

### ⚠️ Critical: App Verification Status

**DirectSonya** (`1841927200521952`) is the app that currently issues working tokens for reading media. However, **as of the latest session, the app does NOT have Advanced Access for `instagram_content_publish`** — this means `POST /media` returns:

```json
{"error": {"message": "(#10) Application does not have permission for this action", "code": 10}}
```

**What this means:**
- `GET /media` (reading posts) works ✅
- `POST /media` (creating story containers) fails ❌

**Resolution paths (in order of speed):**
1. **PostMyPost API** (user already has account, Project ID 297102) — upgrade tariff for API access, then use their endpoint instead of raw Graph API
2. **Business Verification in Meta** — submit `SonyaHermes` or `DirectSonya` for Business Verification at https://developers.facebook.com/apps/ → App Review → Business Verification. Once verified, request **Advanced Access** for `instagram_content_publish`. Timeline: days to weeks.
3. **Alternative verified app** — if user has another Facebook App that is already Business Verified, generate tokens from that app instead.

## How the Script Works

`publish_story.py` does the following:

1. **Reads token** from `~/.hermes/profiles/instamodel/.page_token.txt`
2. **Picks next photo** from `~/.hermes/profiles/instamodel/stories_queue/`
3. **Starts a tunnel** — copies photo to `/tmp/ig_webroot/`, runs `python3 -m http.server 8000`, then launches `cloudflared tunnel --url http://localhost:8000`
4. **Extracts HTTPS URL** from cloudflared output (e.g. `https://xxxx.trycloudflare.com/story.jpg`)
5. **Creates a story container** via `POST /{IG_ID}/media` with `image_url={url}&media_type=STORIES`
6. **Publishes** via `POST /{IG_ID}/media_publish` with `creation_id={container_id}`
7. **Moves file** to `stories_published/` and logs to `stories_log.txt`

## Getting a Page Access Token

### Step 1: Graph API Explorer (short-lived, 1-2 hours)

1. Go to https://developers.facebook.com/tools/explorer
2. Select **App:** `SonyaHermes`
3. Select **User or Page:** `Page` → `Kirakira luna`
4. Add permissions:
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
5. Click **Generate Access Token**
6. Copy the token (starts with `EAA...`)
7. Save to `~/.hermes/profiles/instamodel/.page_token.txt`

### Step 2: Exchange for Long-Lived Token (60 days)

Run:
```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=908058175688398&client_secret=eb917c58eaf5175036eee016bdc0480b&fb_exchange_token={SHORT_LIVED_TOKEN}"
```

Save the returned `access_token` to `.page_token.txt`.

**Pitfall:** If you only use the Explorer token without exchanging, it expires in ~2 hours and the cronjob will start failing silently.

**Pitfall — exchange via Python fails:** The `fb_exchange_token` endpoint sometimes rejects requests made from Python `urllib` with generic "Invalid request" or 400 errors, even with correct credentials. If this happens, use `curl` directly instead:
```bash
curl -s "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token\&client_id=908058175688398\&client_secret=eb917c58eaf5175036eee016bdc0480b\&fb_exchange_token=\${SHORT_TOKEN}"
```
Then save the returned `access_token` manually to `.page_token.txt`.

## Required Setup Before Publishing

```bash
mkdir -p ~/.hermes/profiles/instamodel/stories_queue
mkdir -p ~/.hermes/profiles/instamodel/stories_published
```

Drop `.jpg`/`.png` files into `stories_queue/`. The script publishes one per run.

## Cronjob Setup (3 Stories/day)

Example schedules (US times):
- PT: `0 9,15,21 * * *` (9am, 3pm, 9pm Pacific)
- ET: `0 12,18,0 * * *` (12pm, 6pm, 12am Eastern)

```bash
# Every day at 9am, 3pm, 9pm PT
0 9,15,21 * * * /usr/bin/python3 /root/.hermes/scripts/publish_story.py >> /root/.hermes/profiles/instamodel/cron/stories.log 2>&1
```

**Important:** Only 1 of the 3 daily stories should include text/caption. The current script publishes images only. For text overlays, either:
- Pre-burn text onto images before dropping into queue, OR
- Extend the script to use Instagram's `caption` parameter (limited for Stories — text overlay requires Stories API v2 or manual posting)

## Known Pitfalls

1. **Token type — MUST be Page Access Token** — A User Access Token (even with `instagram_content_publish` scope) will NOT work for publishing. In Graph API Explorer, always switch "User or Page" to **"Page"** → select **"Kirakira luna"** before generating.

2. **App must have Advanced Access for `instagram_content_publish`** — If the Facebook App is NOT Business Verified, `POST /media` returns `(#10) Application does not have permission for this action`. This is a **Meta-level restriction**, not a token issue. Resolution:
   - Submit app for Business Verification at https://developers.facebook.com/apps/ → App Review → Business Verification
   - Or use an already-verified app
   - Or use a third-party service (e.g., PostMyPost) that has already completed verification

3. **Token expiry** — Always exchange for long-lived token. Set a calendar reminder every 50 days.

4. **Cloudflared binary** — Script expects `/tmp/cloudflared`. Download if missing:
   ```bash
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared && chmod +x /tmp/cloudflared
   ```

5. **Rate limits on Page creation** — If Facebook blocks creating new Pages, try:
   - Waiting 24-48 hours
   - Using an existing old Page
   - Creating from a different Facebook account

6. **Instagram Creator → Page linking** — Instagram may also rate-limit linking attempts. Wait 24-72 hours if "temporary restrictions" error appears.

7. **Queue empty** — Script exits cleanly with code 0 when queue is empty. Cron will just skip until photos are added.

8. **Tunnel stability** — Script verifies HEAD request to tunnel URL before proceeding. If unstable, increase `time.sleep()` in `start_tunnel()`.

## Testing Manually

```bash
# 1. Put a test image in queue
cp /path/to/test.jpg ~/.hermes/profiles/instamodel/stories_queue/

# 2. Run script
python3 ~/.hermes/scripts/publish_story.py
```

## Fallbacks if Graph API Fails

If tokens keep expiring or Facebook blocks access:
- **PostMyPost** — User already has account (Project ID 297102). API requires paid tier upgrade.
- **Metricool / Ayrshare** — API-first services, ~$15-18/month. Still require Instagram Creator + Facebook Page.

## References

- `references/graph-api-errors.md` — Collected error messages and fixes from past sessions
