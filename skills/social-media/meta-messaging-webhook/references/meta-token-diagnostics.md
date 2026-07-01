# Meta Token Diagnostics

## Quick Check: Is my token valid?

```bash
TOKEN="your_token_here"
curl -s "https://graph.facebook.com/debug_token?input_token=${TOKEN}&access_token=${TOKEN}" | python3 -m json.tool
```

## Reading the response

### Valid token example (correct type)

```json
{
    "data": {
        "type": "PAGE",
        "is_valid": true,
        "scopes": [
            "pages_messaging",
            "instagram_basic",
            "instagram_manage_messages"
        ],
        "granular_scopes": [...]
    }
}
```

✅ `type: PAGE` — you can send replies.

### Invalid token example

```json
{
    "data": {
        "type": "USER",
        "is_valid": true,
        "scopes": [...]
    }
}
```

❌ `type: USER` — receiving works, **sending replies will fail with 400**.

**Fix**: Open Graph API Explorer, switch token scope to **Page**, query `me/accounts?fields=name,access_token`, and copy the `access_token` from the response body.

## Common error codes when sending

| Error | Meaning | Fix |
|-------|---------|-----|
| `400 Bad Request` | Wrong token type or missing permissions | Verify token type is PAGE |
| `403 Forbidden` | Token lacks required scope | Regenerate with `instagram_manage_messages` and `pages_messaging` |
| `10 — Application does not have permission` | App not approved for messaging | Ensure app is Live and IG account is Business/Creator |
| `OAuthException` | Token expired | Regenerate token |

## Token expiry

Page tokens typically last **60 days**. Track `expires_at` in the debug response.

```bash
# Check expiry
curl -s "https://graph.facebook.com/debug_token?input_token=$TOKEN&access_token=$TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('Expires:', d.get('expires_at')); print('Data access expires:', d.get('data_access_expires_at'))"
```
