---
name: hermes-provider-setup-troubleshooting
description: "Diagnose and fix common Hermes Agent provider connection errors (APIConnectionError, 404, NXDOMAIN). Covers OpenModel.ai, Ollama Cloud, OpenAI‑compatible endpoints."
version: 1.0.0
author: agent
metadata:
  hermes:
    tags: [hermes, configuration, providers, troubleshooting, connection]
---

# Hermes Provider Setup & Troubleshooting

When switching Hermes profiles or models, you may encounter APIConnectionError, NXDOMAIN, or HTTP 404 errors. This skill captures diagnosis steps and fixes.

## Common Symptoms

- `APIConnectionError on openai-api — rebuilt client, waiting …`
- `Could not resolve host: api.openmodel.app` (NXDOMAIN)
- HTTP 404 on `/chat/completions` even though `/models` works (OpenModel.ai)
- `Missing Authentication header` on OpenRouter despite valid‑looking key
- Model works in one profile but fails in another

## Quick Fixes

### 1. Switch to Ollama Cloud (if you have OLLAMA_API_KEY)

```bash
hermes --profile default config set model.provider ollama-cloud
hermes --profile default config set model.default deepseek-v4-flash   # or any Ollama‑supported model
```

Ollama Cloud endpoint is `https://ollama.com/v1` and usually reliable.

### 2. Correct OpenModel.ai endpoint

The default config may point to `https://api.openmodel.app/v1`, which is an unresolvable domain. The correct base URL is:

```bash
hermes --profile default config set model.base_url https://api.openmodel.ai/v1
```

Test connectivity:

```bash
curl -s "https://api.openmodel.ai/v1/models" -H "Authorization: Bearer *** | head -c 300
```

If `/models` returns a list but `/chat/completions` returns 404, the model name may be incorrect or the provider may have changed its API path.

**⚠️ CRITICAL: OpenModel.ai uses a NON-OpenAI-compatible format!**

- Endpoint: `POST https://api.openmodel.ai/v1/responses` (NOT `/v1/chat/completions`)
- Request body uses `"input"` field, NOT `"messages"` array
- Example:
```json
{"model":"deepseek-v4-flash","input":"hello"}
```

This means Hermes cannot use OpenModel.ai out-of-the-box unless Hermes has native support for the `/v1/responses` format.

### 3. OpenRouter setup

OpenRouter uses OpenAI-compatible format with endpoint `https://openrouter.ai/api/v1`.
Keys start with `om-...`. Store in `.env` as `OPENROUTER_API_KEY=om-.....

Setup:
```bash
hermes --profile default config set model.provider openrouter
hermes --profile default config set model.base_url https://openrouter.ai/api/v1
hermes --profile default config set providers.openrouter.api_key om-XXXX
```

Note: OpenRouter may return 401 if the key lacks credits.

Check `~/.hermes/.env` for the relevant key (e.g., `OPENAI_API_KEY`, `OLLAMA_API_KEY`). Use `hermes auth list` to see stored credentials.

### 4. Use interactive model picker

If unsure which provider/model works, run the setup wizard **in an interactive terminal**:

```bash
hermes --profile default setup model
```

This cannot be run through a subprocess pipe; you must execute it directly in the terminal.

## Diagnosis Commands

```bash
# Show current config for a profile
hermes --profile default config

# Check DNS resolution
nslookup api.openmodel.app
nslookup api.openmodel.ai

# Test endpoint reachability
curl -I "https://api.openmodel.ai/v1/chat/completions" -H "Authorization: Bearer $KEY"
curl -I "https://ollama.com/v1/chat/completions" -H "Authorization: Bearer $OLLAMA_API_KEY"

# List available models (good endpoint test)
curl -s "https://api.openmodel.ai/v1/models" -H "Authorization: Bearer $KEY" | jq '.data[].id' | head -5
```

## When the Error Is Profile‑Specific

Hermes stores config per profile. The active session uses `~/.hermes/profiles/<name>/config.yaml`, while the default profile uses `~/.hermes/config.yaml`. Verify each:

```bash
cat ~/.hermes/config.yaml | grep -A5 -B5 "model:"
cat ~/.hermes/profiles/coding/config.yaml | grep -A5 -B5 "model:"
```

If you want to copy a working configuration from one profile to another:

```bash
cp ~/.hermes/profiles/coding/config.yaml ~/.hermes/profiles/default/config.yaml
```

## Fallback: Reset to a Known‑Good Provider

If you cannot diagnose the issue quickly, switch the problematic profile to a provider that you know works in another profile.

Example: `coding` profile uses Ollama Cloud successfully → apply same settings to `default`:

```bash
hermes --profile default config set model.provider ollama-cloud
hermes --profile default config set model.default deepseek-v3.2
hermes --profile default config set model.base_url https://ollama.com/v1
```

## Remember

- **OpenModel.ai** endpoint is `https://api.openmodel.ai/v1`, not `.app`.
- **Ollama Cloud** endpoint is `https://ollama.com/v1`.
- `hermes model` wizard requires an interactive terminal.
- Connection errors often come from DNS (NXDOMAIN) or wrong base_url.
- Check both `~/.hermes/config.yaml` (default profile) and `~/.hermes/profiles/<name>/config.yaml` (named profiles).