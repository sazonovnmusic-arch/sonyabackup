# Meta App Product Selection for Instagram Messaging

## Problem

Creating a Meta app with the wrong product leads to "Application does not have the capability" errors when trying to send DMs or access conversation endpoints.

## Correct Product: Instagram Graph API (NOT Basic Display)

| Product | Can read DMs | Can send replies | Messaging webhooks |
|-----------|-------------|------------------|-------------------|
| **Instagram Graph API** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Instagram Basic Display** | ❌ No | ❌ No | ❌ No |
| **Messenger** | ✅ Via IG connection | ✅ Via IG connection | ⚠️ Only if IG linked |

## How to verify your app has the right product

In Meta for Developers → Your App → Products sidebar:

1. You should see **"Instagram Graph API"** listed
2. Under it: **"API Setup with Instagram Login"** (not just "Basic Display")
3. The connected account shows as **"Instagram Business Account"**

## Symptoms of wrong product

- `me/accounts` returns empty `[]` — no Facebook Page linked through the API
- `/{ig_id}/conversations` returns `(#3) Application does not have the capability`
- `/{ig_id}?fields=connected_facebook_page` returns field-does-not-exist error
- Can receive webhooks but cannot send replies (token is valid but product lacks capability)

## Fix: Switch or recreate the app

If your app only has "Instagram Basic Display":

1. Remove Basic Display product (optional)
2. Add **"Instagram Graph API"** product
3. Re-connect Instagram Business Account under the new product
4. Re-generate Page Access Token
5. Update webhook subscriptions

## Alternative: Use Messenger product with IG connection

Some setups use **Messenger** product instead:
1. Add Messenger product
2. Under Settings → Connected Instagram Accounts
3. Link Instagram Business Account
4. Configure webhook under Messenger → Webhooks
5. Subscribe to `messages` and `messaging_postbacks`

This path also requires a Facebook Page linked to the IG account.

## Facebook Page requirement

Instagram Graph API requires a **Facebook Page** linked to the IG Business/Creator account.

### How to check linkage

Graph API Explorer (with User token):
```
GET me?fields=accounts{name,instagram_business_account}
```

Expected response:
```json
{
  "accounts": {
    "data": [
      {
        "name": "My Page",
        "instagram_business_account": {
          "id": "178414..."
        }
      }
    ]
  }
}
```

If `accounts` is empty or missing `instagram_business_account`:
- The IG account is NOT linked to a Facebook Page through the API
- Fix: In Instagram app → Settings → Account → Linked accounts → Facebook → Link Page

## Field deprecation note

`connected_facebook_page` field on Instagram account object is **deprecated** and returns `(#100) Tried accessing nonexisting field`. Use `me?fields=accounts{instagram_business_account}` instead.
