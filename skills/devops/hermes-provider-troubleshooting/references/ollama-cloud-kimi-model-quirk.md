# Ollama Cloud + kimi-k2.6 Model Name Quirk

Date: 2026-06-20
Profile: default
Provider: ollama-cloud

## Issue

Hermes config set `model: kimi-k2.6:cloud`.
`ollama.com/v1/models` lists model as `kimi-k2.6` (no `:cloud` suffix).
Inference call with `:cloud` suffix → HTTP 401 Unauthorized.
Inference call without suffix → needs testing (likely works if key has inference permission).

## Lesson

When switching to Ollama Cloud for Kimi models, use `kimi-k2.6` (not `kimi-k2.6:cloud`) in the actual API payload.
Hermes aliases may append `:cloud`, but the provider endpoint rejects it.

## Key Rotation

New key set via:
```bash
hermes config set providers.ollama-cloud.api_key "sk-..."
```

Verification:
- Model list: works with new key (lists `kimi-k2.6`, `kimi-k2.5`, `kimi-k2.7-code`)
- Inference: returned 401 — likely key lacks inference quota or wrong plan tier.

## Root Cause Hypothesis

The key works for metadata endpoints (`/v1/models`) but not for `/v1/chat/completions`.
This suggests the Ollama Cloud account associated with this key either:
- Has no active paid plan for inference
- Key is scoped to read-only
- Or key belongs to an account that hasn't added a payment method

## Next Steps (if issue persists)

1. Log into ollama.com with the account that owns this key
2. Check Settings → Billing → Usage/Quota
3. Try generating a fresh key from the same account
4. Consider switching provider to `novita` or `requesty` for kimi-k2.6 if Ollama Cloud continues failing
