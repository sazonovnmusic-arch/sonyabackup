---
name: instagram-messaging-api
description: "Build Instagram DM automation bots using Meta Messaging API + webhooks."
platforms: [linux]
category: social-media
---

# Instagram Messaging API Webhook Bot

## When to use

Use when the user wants to:
- Receive and reply to Instagram DMs automatically
- Build a chatbot for Instagram Business/Creator accounts
- Integrate Instagram messaging into their own backend
- Automate replies, lead capture, or customer support via Instagram

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Instagram Business or Creator account | Personal accounts **do not work** with the API |
| Facebook Page linked to the IG account | Required for API access |
| Meta Developer account | developers.facebook.com |
| HTTPS webhook URL | Meta rejects HTTP-only callbacks |

## Architecture

```
Instagram DM → Meta servers → POST to your HTTPS webhook
                                    ↓
                            Your FastAPI server
                                    ↓
                        Process message + reply via Graph API
```

## Workflow

### 1. Meta App Setup (user does this in browser)

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Create app → select "Other" → "Business"
3. In Products sidebar, add **Instagram**
4. Under Instagram → API Setup, connect the IG Business account
5. Add the IG account as a **Tester** if needed, then accept the invite in Instagram app (Settings → Apps and Websites → Tester Invites)

### 2. Generate Page Access Token

1. In the Meta app dashboard, go to **Instagram → Generate Access Token**
2. Select the connected IG account
3. Copy the token (lives ~60 days, refreshable)
4. This token is used for all API calls — keep it secret

### 3. Deploy Webhook Server (agent does this)

Use the template in `templates/webhook_server.py`. Key points:
- Exposes `GET /webhook` for Meta verification (returns hub.challenge)
- Exposes `POST /webhook` for receiving events
- Verifies signature via `X-Hub-Signature-256` (optional but recommended)
- Replies via `POST https://graph.facebook.com/v18.0/me/messages`

### 4. Expose via HTTPS Tunnel

Meta requires HTTPS. On a VPS without a domain, use **cloudflared quick tunnel**:

```bash
# Download cloudflared (one-time)
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared

# Start tunnel (gives random public HTTPS URL)
/tmp/cloudflared tunnel --url http://localhost:8000
```

The output prints a URL like:
```
https://something.trycloudflare.com
```

**Caveat**: Quick tunnels are ephemeral (change on restart). For production, use a named tunnel or reverse-proxy through your own domain.

### 5. Configure Webhook in Meta

1. In the Meta app → Instagram → Webhooks → Edit Subscriptions
2. Callback URL: `https://<your-tunnel>/webhook`
3. Verify Token: must match the `VERIFY_TOKEN` env var / hardcoded value in your server
4. Subscribe to events: **messages**, **messaging_postbacks**
5. Click "Verify and Save"

### 6. Test

Send a DM to the IG account. The webhook server should receive a JSON payload and reply.

## Pitfalls

### Token Expiration

Page Access Tokens expire in **60 days**. Implement token refresh before expiration or the bot silently stops responding.

### HTTPS Only

Meta strictly rejects HTTP webhook URLs. Localhost testing via HTTP will fail verification. Always use cloudflared, ngrok, or a proper HTTPS reverse proxy.

### IG Account Type

Only **Business** and **Creator** accounts work. If the user has a personal account, they must switch in Instagram settings before connecting to the Meta app.

### Cloudflared Ephemeral URLs

Quick tunnels change URL on every restart. If Meta's webhook verification was done with URL A and you restart the tunnel getting URL B, Meta will keep sending to the old (dead) URL until you update it in the dashboard.

**Fix**: For long-running bots, use a named Cloudflare tunnel or your own domain.

### Message Type Filtering

The webhook receives many event types (story mentions, reactions, etc.). Always check `event.get("message", {}).get("text")` before assuming it's a text DM. Ignore non-text events gracefully.

### Environment Variables Don't Apply to Background Processes

When launching the server with `terminal(background=true)`, exported env vars in the command string are NOT reliably inherited by the background process (depends on shell wrapper). The server starts with empty tokens and fails to reply.

**Fix**: Either:
- Hardcode tokens directly in `webhook_server.py` (quickest for throwaway setups)
- Use a wrapper shell script that exports vars then execs uvicorn
- Write a systemd service file with `Environment=` directives

### `message_edit` and Other Event Types

Meta sends `message_edit` (user edited their DM), `message_reactions`, and `story_mention` events. The default template only handles `message` and `postback`. If you don't account for `message_edit`, the bot may silently drop edited messages.

**Fix**: Check for `message_edit` in addition to `message` when extracting text. See `templates/webhook_server.py` for the updated handler.

### Uvicorn Module Availability in venv

If you create a `venv` but install packages globally (e.g. via `python3 -m pip install` instead of `venv/bin/python -m pip install`), `venv/bin/python -m uvicorn` will fail with "No module named uvicorn". Always install into the same environment that runs the server.

**Quick check**: `python3 -c "import uvicorn; print(uvicorn.__file__)"` — verify it's inside `venv/lib`.

## Reference Files

- `templates/webhook_server.py` — FastAPI webhook server boilerplate
- `references/meta-setup-steps.md` — Detailed screenshots and UI walkthrough

## Related Skills

- `instagram-story-generator` — For creating Story content (image generation), not messaging
