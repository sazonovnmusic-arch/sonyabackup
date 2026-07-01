---
name: hermes-provider-integration
description: "Connect custom LLM providers, API gateways, and third-party endpoints to Hermes Agent profiles."
version: 1.0.0
author: Session
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, providers, openai-compatible, api-gateway, custom-endpoint, openmodel]
    related_skills: [hermes-agent]
---

# Hermes Provider Integration

Connect third-party LLM providers and API gateways to Hermes Agent using OpenAI-compatible, Anthropic-compatible, or custom endpoints.

## When to Use This Skill

- Adding a new provider not in Hermes' built-in list (e.g. OpenModel, Together, Fireworks, Groq via custom base_url)
- Switching an existing profile to a different gateway or model
- Debugging why a custom endpoint isn't responding to Hermes
- Extracting API documentation from SPA-rendered doc sites

## Core Workflow

### 1. Verify Endpoint Health

Before touching Hermes config, confirm the endpoint works with raw curl:

```bash
# List models (OpenAI-compatible)
curl -s https://BASE_URL/v1/models \
  -H "Authorization: Bearer *** \
  | python3 -m json.tool | grep '"id"'

# Test a chat completion
curl -s https://BASE_URL/v1/chat/completions \
  -H "Authorization: Bearer *** \
  -H "Content-Type: application/json" \
  -d '{"model":"MODEL_NAME","messages":[{"role":"user","content":"hi"}]}'
```

If `/v1/models` 404s, try `/v1/chat/completions` directly — some gateways skip the models list.

### 2. Configure Hermes Profile

Two ways: `hermes config set` CLI (preferred by users who like self-service) or hand-editing `~/.hermes/profiles/<name>/hermes.yml`.

**Via CLI:**

```bash
PROFILE=coding
hermes config set model.default MODEL_NAME --profile $PROFILE
hermes config set model.provider openai --profile $PROFILE
hermes config set model.base_url https://BASE_URL/v1 --profile $PROFILE
hermes config set model.api_key *** --profile $PROFILE
```

**Or write to .env (keeps secrets out of YAML):**

```bash
echo 'CUSTOM_API_KEY=*** >> ~/.hermes/profiles/$PROFILE/.env
```

Then reference it in config or let Hermes read it via env interpolation.

### 3. Restart Gateway / Session

Config changes need a fresh session:
- **CLI:** exit and relaunch `hermes --profile <name>`
- **Gateway:** `systemctl --user restart hermes-gateway-<profile>` (or equivalent)
- **Telegram bot:** `/restart` in chat (only works for gateway-managed bots)

### 4. Verify Inside Hermes

Start a new session and run `/model` or `/status` to confirm the active model.

## Provider-Specific Notes

### OpenModel

- **Base URL:** `https://api.openmodel.ai/v1` (NOT `api.openmodel.app` — that string appears on some pages but the canonical endpoint is `api.openmodel.ai`)
- **Auth header:** `Authorization: Bearer *** (OpenAI format)
- **Key prefix:** `om-`
- **Models:** names must match exactly what's shown in the OpenModel Console (e.g. `deepseek-v4-flash`, `claude-sonnet-4-20250514`)
- **DeepSeek access:** DeepSeek models are routed through the Messages (Anthropic) API on OpenModel, but Hermes uses the OpenAI Responses/Chat format. Just specify `model.provider: openai` and `model.base_url: https://api.openmodel.ai/v1` — OpenModel handles protocol translation internally.
- **Free tier caveat:** `deepseek-v4-flash` is currently free on OpenModel but latency is high (~9s average, ~154 tok/s throughput). Test before committing a coding profile to it.
- **SDK docs format:** OpenModel docs are an SPA. Browser snapshots won't render content properly. Use `curl` on the sitemap to enumerate URLs, then fetch each page directly. See `references/openmodel-api-docs.md`.

### Generic OpenAI-Compatible

Most gateways (OpenRouter, Groq, Together, Fireworks, LocalAI) follow the same pattern:
- `provider: openai`
- `base_url: <host>/v1`
- `api_key: <key>`
- model names are provider-specific

## Pitfalls

| Issue | Cause | Fix |
|---|---|---|
| `invalid_api_key` | Wrong base URL or key | Double-check `api.openmodel.ai` vs `openmodel.app`; verify key starts with `om-` |
| `model_not_found` | Model name mismatch | Check exact model ID in provider console, not marketing name |
| High latency with coding | Free-tier overloaded model | Monitor provider's latency dashboard; set fallback provider if possible |
| Config not applied | Forgot to restart | New session required; `/reset` in gateway won't reload model config |
| Endpoint works in curl but Hermes fails | Hermes uses `/v1/chat/completions`, some gateways only support `/v1/responses` or vice versa | Test the exact path Hermes calls; set `model.base_url` with `/v1` suffix |

## SPA Documentation Scraping

Many modern doc sites (Next.js, Nuxt, Docusaurus) render content client-side. Browser snapshots/accessibility trees show only skeletons. Use this pattern:

```bash
# 1. Grab sitemap
curl -s https://docs.example.com/sitemap.xml | \
  grep -oP '<loc>[^<]+' | sed 's|<loc>||'

# 2. Fetch all pages in parallel
for url in $(cat urls.txt); do
  curl -sL --max-time 10 "$url" -o "/tmp/docs/$(basename $url).html"
done

# 3. Strip HTML and read
python3 -c "
import re, sys
text = re.sub(r'<script.*?</script>', '', sys.stdin.read(), flags=re.DOTALL)
text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\\s+', ' ', text)
print(text[:5000])
" < file.html
```

## References

- `references/openmodel-api-docs.md` — Condensed OpenModel API documentation extracted from docs.openmodel.ai
