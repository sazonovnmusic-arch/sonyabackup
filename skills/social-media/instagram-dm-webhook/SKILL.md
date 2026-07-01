---
name: instagram-dm-webhook
description: Build and deploy Instagram DM reply bots using the Meta (Facebook) Graph API webhook flow.
platforms: [linux]
tags: [instagram, webhook, meta, fastapi, bot, messaging]
---

# Instagram DM Webhook Bot

Build a server that **receives Instagram DMs via Meta webhooks** and **sends replies** through the Graph API.

## Trigger

Use when the user wants to:
- Receive and reply to Instagram direct messages automatically
- Build a bot that responds to IG DMs
- Connect Instagram Business/Creator account to a webhook

## Prerequisites (hard requirements)

| Requirement | Why |
|-------------|-----|
| **Instagram Business or Creator account** | Personal accounts cannot use the Messaging API |
| **Facebook Page** linked to the IG account | The IG account must be connected to a FB Page |
| **Meta app with Instagram Graph API** | Not "Instagram Basic Display" — that product is read-only |
| **App Advanced Access** to `instagram_manage_messages` | Without this, the app can receive webhooks but **cannot send replies** |
| **HTTPS callback URL** | Meta requires TLS; localhost will not work |

## Key pitfalls

### 1. Token type: Page vs User
- **User Access Token** (what Graph API Explorer shows by default) → **cannot send DM replies**
- **Page Access Token** (belongs to the Facebook Page) → **required for `POST /{page-id}/messages`**
- To get a Page token in Graph API Explorer: select **User**, run `me/accounts?fields=name,access_token`, copy `access_token` from the **response body** (not the top bar).

### 2. Application capabilities
If you see:
> "(#3) Application does not have the capability to make this API call."

→ The app product is **Instagram Basic Display** or lacks Advanced Access. You need:
- **Instagram Graph API** product added
- **Advanced Access** granted for `instagram_manage_messages` and `pages_messaging`
- This requires App Review or switching the app to **Live** mode

### 3. Temporary tunnels for webhooks
Cloudflare quick tunnels (`cloudflared tunnel --url`) generate **random URLs on every restart**. Meta will invalidate the webhook when the URL changes.

**Options for persistent URL:**
- Cloudflare account + named tunnel (free, stable subdomain)
- ngrok with auth token + domain (paid)
- Your own domain + nginx reverse proxy

## Minimal webhook server (FastAPI)

```python
#!/usr/bin/env python3
import os, json, requests
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "change_me")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
PAGE_ID = os.getenv("PAGE_ID", "")

@app.get("/webhook", response_class=PlainTextResponse)
async def verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    if hub_mode != "subscribe" or hub_verify_token != VERIFY_TOKEN:
        raise HTTPException(status_code=403)
    return hub_challenge

@app.post("/webhook")
async def receive_event(request: Request):
    data = await request.json()
    for entry in data.get("entry", []):
        for ev in entry.get("messaging", []):
            sender = ev.get("sender", {}).get("id")
            text = ev.get("message", {}).get("text", "")
            if text:
                reply_to_instagram(sender, f"Echo: {text}")
    return JSONResponse({"status": "ok"})

def reply_to_instagram(recipient_id: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": PAGE_ACCESS_TOKEN,
    }
    requests.post(url, json=payload, timeout=15)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
```

## Workflow

1. **Prepare accounts**: ensure IG is Business/Creator and linked to a FB Page.
2. **Create Meta app**: add product **Instagram Graph API** (not Basic Display).
3. **Add IG account** as a tester in the app, accept the invite in IG settings.
4. **Generate Page Access Token** via Graph API Explorer (`me/accounts`).
5. **Deploy webhook server** with HTTPS endpoint.
6. **Subscribe webhook** in Meta app: paste callback URL + verify token, enable `messages` and `messaging_postbacks`.
7. **Send a test DM** — confirm incoming payload in logs.
8. **Fix token/app-capability issues** if reply fails (see Pitfalls above).
9. **Move to persistent tunnel** before production.

## References

- `references/meta-app-setup.md` — step-by-step screenshot-free guide for Meta app configuration and permission checks.
- `templates/webhook_server.py` — copy-paste FastAPI scaffold with HMAC signature verification.

## See also

- `youtube-content` — if you need to extract transcripts from tutorial videos (e.g. Meta webhook setup guides).
