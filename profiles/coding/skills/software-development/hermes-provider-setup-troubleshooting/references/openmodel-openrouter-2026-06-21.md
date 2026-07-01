# OpenModel.ai & OpenRouter Findings (2026‑06‑21)

## Key Discoveries

### 1. OpenModel.ai API Structure
). The server `api.openmodel.ai` responds to `/v1/models` but returns 404 for all OpenAI‑compatible paths:
- `/v1/chat/completions` → 404
- `/openai/v1/chat/completions` → 404  
- `/api/v1/chat/completions` → 404
. The error message: `{"success":false,"data":null,"error":{"code":"NOT_FOUND","msg":"route not found"}}`

**Conclusion**: OpenModel.ai's public API is **not OpenAI‑compatible** by default. They likely require a different request format, custom headers, or use a private gateway URL.

### 2. OpenModel.ai API Format (CRITICAL — Non-OpenAI-Compatible)

After further investigation on 2026-06-21, discovered that OpenModel.ai uses a **proprietary `/v1/responses` endpoint**, NOT OpenAI-compatible `/v1/chat/completions`.

**Confirmed working endpoint:**
```
POST https://api.openmodel.ai/v1/responses
```

**Request format:**
```json
{
  "model": "deepseek-v4-flash",
  "input": "hello"
}
```

**Response format (error example with wrong key):**
```json
{"error":{"code":"invalid_api_key","message":"invalid api key","type":"invalid_request_error"}}
```

**Important:** This endpoint uses `"input"` string field, NOT `"messages"` array. Hermes Agent does not natively support this format. To use OpenModel.ai with Hermes, either:
- Wait for Hermes to add native OpenModel.ai provider support
- Use a proxy/translator script that converts OpenAI format to OpenModel format
- Use OpenModel.ai's own SDK if available

**Known available models via Ollama Cloud mirror (same models, OpenAI format):**
- deepseek-v4-flash ✅
- deepseek-v4-pro ✅
- deepseek-v3.2 ✅
- kimi-k2.6 ✅ (but may return empty responses)
Keys starting with `om-` (e.g., `om-4ZR6Po2i4aU3Vyj9bh9HtdJqtTHmtjNqqnYVJRcB`) are **OpenRouter keys**, not OpenAI keys. OpenRouter may require:
- Different authorization header (`X-API-Key` instead of `Authorization: Bearer`)
- Account credits/balance (returns "Missing Authentication header" if zero)
- Model names with provider prefix (e.g., `deepseek/deepseek-v4-flash`)

### 3. Ollama Cloud as Fallback
The OPC key (`OLLAMA_API_KEY`) works with Ollama Cloud (`https://ollama.com/v1`) and supports:
1. deepseek-v4-flash
2. deepseek-v4-pro  
3. deepseek-v3.2
4. deepseek-v3.1:671b

### 4. Search Patterns for Unknown APIs
When documentation is missing:
- Test all common endpoint/path combinations programmatically
- Check `/models` endpoint first — if it works, API is alive but path may differ
- Search GitHub repositories for API examples
- Check DNS resolution (`nslookup`, `dig`) for unreachable hosts

## Tested Endpoints & Results

| Endpoint | Status | Notes |
|----------|--------|-------|
| `https://api.openmodel.ai/v1/models` | ✅ 200 | Lists models |
| `https://api.openmodel.ai/v1/chat/completions` | ❌ 404 | Route not found |
| `https://api.openmodel.ai/openai/v1/chat/completions` | ❌ 404 | Route not found |
| `https://api.openmodel.app/v1` | ❌ NXDOMAIN | Domain does not exist |
| `https://ollama.com/v1/models` | ✅ 200 | Lists Ollama Cloud models |
| `https://openrouter.ai/api/v1/models` | ✅ 200 | Lists OpenRouter models |

## Configuration Snippets

### Working Ollama Cloud Config
```yaml
model:
  default: deepseek-v4-flash
  provider: ollama-cloud
  base_url: https://ollama.com/v1
providers:
  ollama-cloud:
    api_key: 38c71ccddefb497883c126afb0313d3e.X94cpm1AvO90KFkGle_tHN7o
```

### OpenRouter Attempt (failed)
```yaml
model:
  default: deepseek/deepseek-v4-flash
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
providers:
  openrouter:
    api_key: om-4ZR6Po2i4aU3Vyj9bh9HtdJqtTHmtjNqqnYVJRcB
```

## Next Steps for OpenModel.ai
1. Contact support for correct API endpoint and format
2. Check if they provide OpenAPI/Swagger documentation
3. Test with different headers (`X-OpenModel-API-Key`, etc.)
4. Look for private gateway URL in account dashboard