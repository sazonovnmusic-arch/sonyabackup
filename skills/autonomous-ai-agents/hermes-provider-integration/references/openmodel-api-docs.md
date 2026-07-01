# OpenModel API — Condensed Reference

Extracted from https://docs.openmodel.ai (SPA, fetched via sitemap + curl).

## What Is OpenModel

Unified AI API gateway. One API key → multiple providers through OpenAI, Anthropic, or Gemini compatible endpoints.

Supported providers: OpenAI, Anthropic, Google Gemini, DeepSeek, DashScope (Alibaba), Xiaomi (MiMo), Kimi, MiniMax, Zai (8+).

## API Protocols

| Protocol | Endpoint | Compatible With | Providers Served |
|---|---|---|---|
| OpenAI Responses | POST /v1/responses | OpenAI SDK | OpenAI, DashScope |
| Anthropic Messages | POST /v1/messages | Anthropic SDK | Anthropic, DeepSeek, DashScope, Xiaomi, Kimi, MiniMax, Zai |
| Gemini | POST /v1beta/models/{model}:generateContent | Google GenAI SDK | Gemini |

DeepSeek, DashScope, Xiaomi, Kimi, MiniMax, Zai — all accessible through Messages API using Anthropic SDK; only model name changes.

## Authentication

- API key prefix: `om-`
- Created at: console.openmodel.ai
- OpenAI format header: `Authorization: Bearer om-xxx`
- Anthropic format header: `X-Api-Key: om-xxx` (preferred) or `Authorization: Bearer om-xxx`
- Gemini format header: `X-Goog-Api-Key: om-xxx` (preferred) or `?key=om-xxx`

## Base URL

`https://api.openmodel.ai`

Note: some pages mention `api.openmodel.app/v1` — canonical endpoint is `api.openmodel.ai`.

## Example Calls

### OpenAI Format (Responses API)
```bash
curl https://api.openmodel.ai/v1/responses \
  -H "Authorization: Bearer $OPENMODEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "input": "Hello, who are you?"}'
```

### Anthropic Format (Messages API)
```bash
curl https://api.openmodel.ai/v1/messages \
  -H "x-api-key: $OPENMODEL_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### DeepSeek via Messages API
Same Anthropic code, just change model name to `deepseek-chat`, `deepseek-reasoner`, etc.

## Streaming

All formats support SSE via `stream: true`.

- OpenAI: `data:` lines, ends with `data: [DONE]`
- Anthropic: named event types
- Gemini: `streamGenerateContent?alt=sse`

## Billing

- Pay-per-token: input, output, cache read, cache write, reasoning tokens
- Internal precision: microdollars (1 USD = 1,000,000 µ$)
- Tiered pricing: threshold tiers (above_128k, above_200k, above_256k) and range tiers (DashScope progressive brackets)

## Rate Limits

- RPM (requests/min) and TPM (tokens/min)
- Enforced at user-level (by group) and channel-level (per upstream endpoint)
- Algorithm: Fixed Window
- Pre-request TPM estimate (tokenizer or length/4 heuristic), corrected after response
- Exceeded → 429 Too Many Requests

## Error Codes (Web API)

| Code | HTTP | Meaning |
|---|---|---|
| BAD_REQUEST | 400 | Malformed request |
| UNAUTHORIZED | 401 | Invalid/missing credentials |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Endpoint doesn't exist |
| TOO_MANY_REQUESTS | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAIL | 503 | Temporarily unavailable |

Proxy endpoints return errors in the format of the requested API (OpenAI/Anthropic/Gemini).

## DeepSeek V4 Flash Free Event

- Currently FREE on OpenModel (input/output/cache all $0)
- Context: 1M tokens, output: 8.2K
- Average latency: ~9,138ms
- Throughput: ~154.3 tok/s
- Support: vision, function calling, streaming, structured output, tool choice, prompt caching, system messages, parallel tools

## SDK Configuration

### OpenAI SDK
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.openmodel.ai/v1", api_key="om-xxx")
```

### Anthropic SDK
```python
import anthropic
client = anthropic.Anthropic(base_url="https://api.openmodel.ai", api_key="om-xxx")
# Note: no /v1 suffix — SDK appends /v1/messages automatically
```

## Model Name Examples

- `gpt-4o`, `gpt-4o-mini`
- `claude-sonnet-4-20250514`, `claude-haiku-4-20250414`
- `gemini-2.0-flash`
- `deepseek-chat`, `deepseek-reasoner`
- `qwen3-max`
- `mimo-v2.5-pro`, `mimo-v2-flash`
