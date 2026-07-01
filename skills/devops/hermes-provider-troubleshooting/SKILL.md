---
name: hermes-provider-troubleshooting
description: |
  Diagnose and fix LLM provider connectivity issues in Hermes Agent —
  expired API keys, 401/403 errors, model name mismatches, and base URL problems.
trigger:
  - User reports "Unauthorized", "401", "API key rejected", or "AuthenticationError"
  - Need to rotate or update an LLM provider API key
  - Model works in list but fails on chat/inference
  - Switching providers or debugging why a model stopped responding
  - Gateway shows provider errors in logs after server restart or migration
---

# Hermes Provider Troubleshooting

## Quick Checks

1. **Which profile is failing?**
   Check `~/.hermes/profiles/<name>/logs/` or `~/.hermes/logs/gateway.log` for provider name and model.

2. **Is the key set in the right place?**
   Hermes stores provider keys in `~/.hermes/config.yaml` (not always `.env`).
   ```bash
   hermes config get providers.<provider>.api_key
   ```

## Updating API Keys

**Correct way — use the CLI:**
```bash
hermes config set providers.<provider>.api_key "sk-..."
```

**Do NOT try to read/write `~/.hermes/.env` directly.**
The `.env` file is a credential store — `read_file` is blocked for defense-in-depth.
Use `terminal` if you must bypass, but prefer the CLI.

## Testing the Key (Critical Pitfall)

A common trap: the *model list* endpoint works, but the *inference/chat* endpoint returns 401.
This means the key is valid for metadata but not for actual usage (wrong plan, expired trial, or provider changed scope).

**Always test inference, not just listing:**
```python
import urllib.request, json
req = urllib.request.Request(
    '<BASE_URL>/v1/chat/completions',
    data=json.dumps({
        'model': '<MODEL_NAME_WITHOUT_SUFFIXES>',
        'messages': [{'role': 'user', 'content': 'hi'}],
        'max_tokens': 5
    }).encode(),
    headers={'Authorization': 'Bearer <KEY>', 'Content-Type': 'application/json'},
    method='POST'
)
```

## Model Name Mismatches

Hermes config may use model aliases like `kimi-k2.6:cloud`.
The provider API may expect `kimi-k2.6` or `moonshotai/kimi-k2.6`.

| Symptom | Likely Cause |
|---------|-------------|
| 401 on chat, but model list loads | Key lacks inference permissions |
| 404 on model | Wrong model ID for that provider endpoint |
| 401 on everything | Key fully dead/wrong account |

**Find the canonical model ID:**
```bash
curl -s -H "Authorization: Bearer $KEY" "$BASE_URL/v1/models" | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"
```

## Custom Providers (e.g. OpenModel, proxy endpoints)

Hermes supports arbitrary OpenAI-compatible endpoints via `custom_providers:` in `config.yaml`:
```yaml
custom_providers:
- name: deepseek-v4-flash
  base_url: https://api.openmodel.app/v1
  api_key: om-...YOUR_KEY...
  model: deepseek-v4-flash
```
Then set the model as default or alias:
```bash
hermes config set model.default deepseek-v4-flash
```

### What is "Display Name"?

In Hermes CLI interactive flows (`hermes setup` or custom provider wizard), you may be prompted for a **Display Name**. This is purely cosmetic — the human-readable label shown in provider pickers and `/info` output. It has zero effect on authentication.

| Field | Purpose | Required? |
|---|---|---|
| `name` (or Display Name) | Label in UI | No — falls back to provider key |
| `provider_key` | Internal dictionary key (v12+ `providers:`) | Yes for deduplication |
| `base_url` | Where to send API requests | Yes |
| `api_key` / `key_env` | Credentials | Yes |

If you see "Display name" during setup, enter anything memorable (e.g., `OpenModel`). It won't fix or break a 401.

### `custom_providers:` vs `providers:` (v12+ schema)

Hermes supports two config shapes:

**Legacy list (`custom_providers:`):**
```yaml
custom_providers:
- name: deepseek-v4-flash
  base_url: https://api.openmodel.app/v1
  api_key: om-...
  model: deepseek-v4-flash
```

**Modern keyed dict (`providers:`):**
```yaml
providers:
  openmodel:
    name: OpenModel
    api: https://api.openmodel.app/v1
    api_key: om-...
    default_model: deepseek-v4-flash
```

Both are normalized at runtime by `get_compatible_custom_providers()`. Use whichever your `config.yaml` already has.

**Pitfall:** `hermes setup` is a **full wizard** that re-runs every step (provider → model → Telegram → Discord → ...). It will overwrite your model and may regenerate tokens. To simply switch models without touching Telegram config, always use:
```bash
hermes model        # interactive picker
hermes config set model.default <model-id>   # direct override
```
Never suggest `hermes setup` when the user just wants to change models.

### DNS-first diagnostic rule (critical)
When a custom provider fails with **"Connection error"** (not 401/403):
1. **Resolve the hostname manually BEFORE assuming bad key:**
   ```bash
   dig @8.8.8.8 api.example.com +short
   curl -sI https://api.example.com/v1 --connect-timeout 10
   ```
2. If DNS returns empty → **service-side outage**, not your key.
3. If DNS resolves but curl returns 530 (Cloudflare) → **upstream origin down**, report to provider.
4. If DNS resolves and HTTP code is 401/403 → **then** investigate the key.

### 401 vs Connection Error: decision tree
| Symptom in logs | Root cause | Fix |
|-----------------|------------|-----|
| `APIConnectionError: Connection error.` | Host unreachable / DNS fail / TLS block | Check DNS, firewall, base_url typo |
| `AuthenticationError: 401 Unauthorized` | Bad or expired API key | Rotate key in provider dashboard |
| `AuthenticationError: 403 Forbidden` | Key valid but lacks model permissions | Upgrade plan or change model |
| `404 Not Found` | Wrong `model` name for that endpoint | Hit `/v1/models` to find canonical ID |

### Testing a custom provider
Always test the full inference endpoint, not just the base URL:
```bash
curl -s https://api.openmodel.app/v1/chat/completions \
  -H "Authorization: Bearer *** \"  \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}],"max_tokens":5}' \
  --connect-timeout 15
```

## `model.api_key` vs `providers.*.api_key` — Location Matters

When a user manually edits `config.yaml` or runs `hermes config set`, they sometimes accidentally place the key in the wrong nest.

```yaml
# WRONG — key sits at model level, provider lookup may miss it
model:
  default: deepseek-v4-flash
  provider: openmodel
  api_key: om-...          # ← Hermes may ignore this for provider resolution

# RIGHT — key belongs inside the provider definition
providers:
  openmodel:
    api: https://api.openmodel.app/v1
    api_key: om-...        # ← runtime reads from here
    default_model: deepseek-v4-flash
```

**Symptoms of misplaced key:**
- `hermes config get providers.openmodel.api_key` returns `null` or empty
- Model list works (no key needed for `/v1/models` on some hosts) but chat calls get 401
- Switching providers suddenly breaks because the old `model.api_key` leaks into the new provider

**Fix:** Move the key into the provider block:
```bash
hermes config set model.api_key ""              # clear stray key
hermes config set providers.openmodel.api_key "om-..."
```

## Syncing Provider Config Across Profiles

Hermes profiles (`~/.hermes/profiles/<name>/`) each have their own `config.yaml`. Adding a provider to `~/.hermes/config.yaml` (default profile) does **not** automatically copy it to coding, youtube, or traffic profiles.

**Symptom:** Coding bot works on DeepSeek v3.2, but you want it to use the same model as default (e.g., kimi-k2.6:cloud).

**Fix:** Propagate the provider entry and model settings to the target profile:

```bash
# Option A: Copy the entire provider block with Python/yaml
python3 -c "
import yaml
with open('/root/.hermes/config.yaml') as f:
    src = yaml.safe_load(f)
with open('/root/.hermes/profiles/coding/config.yaml') as f:
    dst = yaml.safe_load(f)

# Copy provider entry
if 'providers' in src and 'ollama-cloud' in src['providers']:
    dst.setdefault('providers', {})['ollama-cloud'] = src['providers']['ollama-cloud']

# Update model block
dst['model'] = {
    'default': src['model'].get('default'),
    'provider': src['model'].get('provider'),
    'base_url': src['model'].get('base_url'),
}

with open('/root/.hermes/profiles/coding/config.yaml', 'w') as f:
    yaml.dump(dst, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
"

# Option B: Direct CLI per profile
hermes config set model.default kimi-k2.6:cloud --profile coding
hermes config set model.provider ollama-cloud --profile coding
```

**Pitfall:** `--profile` flag is not universally supported in all `hermes config` subcommands. If CLI rejects it, use Option A (Python script) or manually edit `~/.hermes/profiles/<name>/config.yaml`.

## Systemd Restart Hangs (SIGTERM Timeout)

Hermes gateway services occasionally refuse to die on `systemctl restart`, causing a 15–90 second hang.

**Root cause:** `TimeoutStopSec=90s` in the systemd unit, but `drain_timeout=180s` in Hermes config. The gateway tries to drain sessions longer than systemd allows, so systemd escalates to SIGKILL.

**What it looks like:**
```
# systemctl restart hermes-gateway-coding
# → hangs, no prompt
Active: deactivating (stop-sigterm) since ... 30s ago
Main PID: 24882
```

**Fix:**
```bash
# Wait briefly, then force-kill if still stuck
systemctl restart hermes-gateway-coding
sleep 5
systemctl status hermes-gateway-coding | grep -q "deactivating" && sudo kill -9 $(systemctl show hermes-gateway-coding -p MainPID --value)
# Then restart cleanly
systemctl start hermes-gateway-coding
```

**Permanent fix:** Regenerate the unit with correct timeouts:
```bash
hermes gateway service install --replace --profile coding
```

## Provider-Specific Notes

### Ollama Cloud
- Base URL: `https://ollama.com/v1`
- Key variable: `OLLAMA_API_KEY`
- Models may need `:cloud` removed from the API payload.
- If inference 401s but list works → key valid for metadata only; check Ollama Cloud billing/plan.

#### Model Exists in Library but 404 via API
A model may be listed at `https://ollama.com/library/<name>` yet return `HTTP 404: model "<name>" not found` from the `/v1` API endpoint.

**Diagnosis:**
```bash
# 1. Check if the model is on the website (may show YES)
curl -sI https://ollama.com/library/ornith | head -1

# 2. Check if it appears in the API model list (may show NO)
curl -s -H "Authorization: Bearer $OLLAMA_API_KEY" https://ollama.com/v1/models | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin).get('data',[])]"

# 3. Try a direct inference call (may return 404)
curl -s -X POST https://ollama.com/v1/chat/completions \
  -H "Authorization: Bearer $OLLAMA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<name>","messages":[{"role":"user","content":"hi"}]}'
```

**Root cause:** Ollama Cloud API (`ollama.com/v1`) does not expose every model from the public library. Some models are web-only, restricted, or gated behind a different endpoint.

**Fix:** Switch to a model that IS returned by the `/v1/models` endpoint. Common available models include: `kimi-k2.6`, `kimi-k2.7-code`, `deepseek-v3.1:671b`, `mistral-large-3:675b`, `gemini-3-flash-preview`, `devstral-2:123b`.

**Pitfall:** Do NOT assume `ollama.com/library/<name>` availability implies API availability. Always verify via `/v1/models` before setting the model in Hermes config.

### OpenRouter
- Base URL: `https://openrouter.ai/api/v1`
- Keys can be restricted by IP or domain in OpenRouter dashboard.

### Gemini / Google
- Uses `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- Quota limits often cause 429, not 401.

## Restart After Key Change

Gateway caches model metadata. After updating a key:
```bash
hermes gateway restart
```
or restart the systemd service:
```bash
systemctl restart hermes-gateway-<profile>
```

## Pitfalls

- **`.env` is not the source of truth for provider keys** in modern Hermes versions — `config.yaml` is.
- **Model list working ≠ inference working** — always test a chat call.
- **`:cloud`/`:fast` suffixes** are Hermes aliases; the raw API may reject them.
- **Don't over-engineer remote Desktop/API Server setups** when the immediate need is just a Telegram bot fix. Ask "what's the simplest path?" before building tunnels and dashboards.
- **`hermes setup` is a FULL wizard** — it re-runs every step (provider → model → Telegram → Discord → ...) even when everything is already configured. For a quick model change, use `hermes model` (interactive picker) or `hermes config set model.default <name>`. Never suggest `hermes setup` to a user who just wants to switch models.
- **API Server is not a standalone `hermes serve` command** — it's a gateway platform adapter (`api_server.py`) that must be loaded by the gateway process. Enabling it requires a gateway restart with the platform active. It is not a quick toggle. Don't attempt to launch it on-the-fly without understanding the gateway lifecycle.
- **Don't restart gateways by killing `hermes gateway` without the `-p <profile>` flag** — this may kill the wrong profile. Always specify the profile: `pkill -9 -f "hermes -p traffic gateway"`.
- **Check `systemctl status` before manual restarts** — if the service is `failed` or `inactive`, use `systemctl start` rather than spawning duplicate manual processes that conflict with systemd.

## Verification Script

Use the companion script to validate a provider key:
```bash
python3 ~/.hermes/skills/hermes-provider-troubleshooting/scripts/test_provider_key.py \
  --provider ollama-cloud \
  --key "$OLLAMA_API_KEY" \
  --model kimi-k2.6
```
(See `scripts/test_provider_key.py` in this skill directory.)
(See `references/openmodel-outage-dns-analysis.md` for a real-world case study of DNS-level provider outage — OpenModel, 2026-06-21.)
