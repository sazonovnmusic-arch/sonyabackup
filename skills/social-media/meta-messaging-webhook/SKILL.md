---
name: meta-messaging-webhook
description: "Set up and operate Instagram/Facebook Messenger webhooks for receiving and replying to DMs via Meta Graph API."
platforms: [linux]
---

# Meta Messaging Webhook Integration

## When to use

Use when the user wants to:
- Receive Instagram DMs programmatically
- Auto-reply to Instagram/Facebook Messenger messages
- Build a bot for Meta platforms (Instagram Business/Creator accounts only)
- Set up webhook infrastructure for Meta Graph API events

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Instagram account | **Business or Creator** — personal accounts do not work |
| Facebook Page | Must be linked to the IG Business account |
| Meta Developer account | https://developers.facebook.com |
| HTTPS endpoint | Meta requires SSL; localhost will not work |

## Quick-start: Webhook Server

### 1. Bootstrap the server

Install deps (system Python or venv):
```bash
python3 -m pip install fastapi uvicorn requests
```

Create `/opt/meta_webhook/webhook_server.py` from `templates/meta_webhook_server.py` (see linked templates).

### 2. Expose via tunnel (quick test)

```bash
# Download cloudflared if missing
curl -sL https://github.com/cloudflare/cloudflared/releases/download/2025.6.0/cloudflared-linux-amd64 -o /tmp/cloudflared
chmod +x /tmp/cloudflared

# Run temporary tunnel (URL changes every restart!)
/tmp/cloudflared tunnel --url http://localhost:8000
```

Copy the HTTPS URL it prints and use that as the Callback URL in Meta.

### 3. Meta App Configuration

1. Create app at https://developers.facebook.com/apps
2. Add **Instagram** product — make sure it's **Instagram Graph API**, NOT "Instagram Basic Display" (see `references/meta-app-product-selection.md`)
3. Link IG Business account under API Setup
4. Go to **Webhooks → Edit Subscriptions**
5. Callback URL = `https://<tunnel>/webhook`
6. Verify Token = whatever you set in the server code
7. Enable subscriptions: `messages`, `messaging_postbacks`
8. Switch app to **Live** mode

### 4. Generate Page Access Token

**Critical**: Meta requires a **Page Access Token**, not a User token.

1. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app → select **Page** (not User) in the token selector
3. Query: `me/accounts?fields=name,access_token`
4. Copy the `access_token` from the response body — **not** the token in the explorer header

If `me/accounts` returns empty `[]`, the IG account is not linked to a Facebook Page. See Pitfall "Missing Facebook Page linkage" below.

### 5. Test end-to-end

Send a DM to the IG account. You should see a POST hit your `/webhook` endpoint.

## Pitfalls

### Token type confusion (most common failure)

Symptom: Receiving messages works, but sending replies fails with `400 Bad Request`.

**Root cause**: You are using a User Access Token instead of a Page Access Token.

**Diagnostic** — hit the debug endpoint:
```bash
curl -s "https://graph.facebook.com/debug_token?input_token=$TOKEN&access_token=$TOKEN"
```

If `"type": "USER"` — wrong token. If `"type": "PAGE"` — correct.

**Fix**: Regenerate via Graph API Explorer selecting Page scope (see Step 4 above).

### Wrong Meta app product selected

Symptom: Webhooks receive messages fine, but any Graph API call to the IG account returns `(#3) Application does not have the capability` or `me/accounts` returns empty `[]`.

**Root cause**: The app was created with **Instagram Basic Display** product (or similar) instead of **Instagram Graph API**.

**Fix**: Check Products sidebar in Meta app dashboard. You need **Instagram Graph API** (not Basic Display). If wrong product is installed, remove it and add the correct one, then re-connect the IG account and regenerate the token. See `references/meta-app-product-selection.md`.

### Missing Facebook Page linkage

Symptom: `me/accounts` returns `{"data": []}` — no Pages found. Instagram account exists but no Page Access Token can be generated.

**Root cause**: The Instagram Business/Creator account is **not linked** to a Facebook Page through the API.

**Diagnostic**:
```
GET me?fields=accounts{name,instagram_business_account}
```
If `instagram_business_account` is missing, the IG account is not linked.

**Fix**: In Instagram app → Settings → Account → Linked accounts → Facebook → Link a Page. Then re-query `me/accounts`.

### Cloudflare quick tunnels are ephemeral

Symptom: Webhook stops working after server restart; Meta shows "Callback verification failed".

**Root cause**: `/tmp/cloudflared tunnel --url` generates a new random subdomain every run.

**Fixes** (in order of preference):
1. **Named tunnel with Cloudflare account** (free): create a persistent tunnel at https://dash.cloudflare.com
2. **ngrok with auth token** ($8/mo): get a fixed subdomain
3. **Your own domain + nginx**: reverse-proxy to localhost:8000, add SSL via certbot

For quick testing: just re-verify the new URL in Meta each time. For production: use option 1 or 3.

### Missing permissions

Required granular scopes for Instagram messaging:
- `instagram_basic`
- `instagram_manage_messages`
- `pages_messaging`
- `pages_read_engagement`

If any are missing, regenerate the token with those permissions checked.

### App in Development mode

If the app is in **Development** mode, only testers can trigger webhooks. Switch to **Live** mode to receive messages from all users.

## Verification

After setup, verify each layer:

| Check | Command / Action |
|-------|-----------------|
| Server running | `curl http://localhost:8000/health` |
| Tunnel alive | `curl https://<tunnel>/health` |
| Webhook verify | `curl "https://<tunnel>/webhook?hub.mode=subscribe&hub.verify_token=$VT&hub.challenge=test"` → should return `test` |
| Token valid | `curl "https://graph.facebook.com/debug_token?input_token=$TOKEN&access_token=$TOKEN"` |
| Token type | Look for `"type": "PAGE"` in debug output |
| Page linked | `curl "https://graph.facebook.com/v18.0/me?fields=accounts{name,instagram_business_account}&access_token=$TOKEN"` |
| Send capability | Send yourself a DM, check server logs for POST + reply success |

## Template Files

- `templates/meta_webhook_server.py` — starter FastAPI webhook server with verification, signature checking, and reply helpers
- `references/meta-token-diagnostics.md` — expanded token troubleshooting guide
- `references/meta-app-product-selection.md` — choosing the right Meta app product (Graph API vs Basic Display vs Messenger)

## Related

- Meta Graph API docs: https://developers.facebook.com/docs/messenger-platform/instagram
- Webhook reference: https://developers.facebook.com/docs/graph-api/webhooks
