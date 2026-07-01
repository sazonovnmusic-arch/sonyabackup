# OpenModel outage analysis — 2026-06-21

## Symptom
Custom provider `deepseek-v4-flash` via OpenModel configured in Hermes with:
```yaml
custom_providers:
- name: deepseek-v4-flash
  base_url: https://api.openmodel.app/v1
  api_key: om-6vD6GeAuJuARr1acaGeGqNJPDQEuptCRXFzBNjtW
  model: deepseek-v4-flash
```

Hermes logs showed repeated `APIConnectionError: Connection error.` (not 401/403).
User initially thought it was an auth error.

## Root cause (confirmed by diagnosis)

1. **DNS resolution failure**: `api.openmodel.app` does NOT resolve via any public DNS (tested `dig @8.8.8.8 api.openmodel.app +short` → empty).
2. **Parent domain alive but broken**: `openmodel.app` resolves to Cloudflare (188.114.96.1 / 188.114.97.1), but direct HTTP request to `https://openmodel.app/v1/chat/completions` returns **HTTP 530** (Cloudflare origin unreachable).
3. **Conclusion**: service-side total outage on OpenModel's end. Not a config or key problem.

## Diagnostic steps that proved it

```bash
# Step 1: DNS check
dig @8.8.8.8 api.openmodel.app +short        # → empty (bad)
dig @8.8.8.8 openmodel.app +short            # → 188.114.96.1 (parent OK)

# Step 2: HTTP probe to parent
curl -sI https://openmodel.app/v1/chat/completions -H "Authorization: Bearer KEY"
# → HTTP/2 530 (Cloudflare origin error)

# Step 3: Direct endpoint
curl -sI https://api.openmodel.app/v1
# → exit code 6: Could not resolve host
```

## Lesson
When a custom provider fails with "Connection error" (not auth error), always do DNS + HTTP probe first before blaming the API key. Saves time and avoids unnecessary key rotation.

## Provider info (as of 2026-06-21)
- Docs: https://docs.openmodel.ai/en
- Claimed base URL: https://api.openmodel.app/v1 (OpenAI compatible)
- Status: fully down (DNS + origin)
