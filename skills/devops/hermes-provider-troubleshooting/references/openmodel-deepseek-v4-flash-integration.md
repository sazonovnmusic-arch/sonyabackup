# OpenModel + DeepSeek-V4-Flash Integration Notes

Extracted from docs.openmodel.ai and user session 2026-06-21.

## Base URL

```
https://api.openmodel.app/v1
```

Confirmed from OpenModel docs home page (`export OPENAI_BASE_URL="https://api.openmodel.app/v1"`).

## Auth Header Format

Standard Bearer token:
```
Authorization: Bearer om-xxx...
```

Key format: `om_` or `om-` prefix (user-supplied keys used `om-`).

## DeepSeek-V4-Flash Promo (Limited-Time Free)

| Detail | Value |
|---|---|
| Model | `deepseek-v4-flash` |
| Price (promo) | **$0.00 / M input + output** |
| Normal price | $0.035/M input, $0.07/M output |
| Promo validity | Until approx. 2026-06-28 (per promotional banner) |
| Source | OpenModel promotional banner / Telegram channels |

## Hermes Config Format

### Option 1: Legacy `custom_providers:` list
```yaml
custom_providers:
- name: deepseek-v4-flash
  base_url: https://api.openmodel.app/v1
  api_key: om-YOUR_KEY_HERE
  model: deepseek-v4-flash
```

### Option 2: Modern v12+ `providers:` keyed dict (RECOMMENDED)
```yaml
providers:
  openmodel:
    name: OpenModel
    api: https://api.openmodel.app/v1
    api_key: om-YOUR_KEY_HERE
    default_model: deepseek-v4-flash
```

Both are normalized at runtime by `_normalize_custom_provider_entry()`. Use whichever your `config.yaml` already has.

### ⚠️ CRITICAL: `model.api_key` is NOT the same as `providers.*.api_key`

When a user runs `hermes config set model.api_key "om-..."`, the key lands at the **model** level, not the **provider** level. Many provider lookups read from `providers.<name>.api_key`, so a misplaced key causes 401 even though the key itself is valid.

**Wrong placement (leads to 401):**
```yaml
model:
  default: deepseek-v4-flash
  provider: openmodel
  api_key: om-...          # ← Hermes ignores this during provider resolution
```

**Right placement:**
```yaml
providers:
  openmodel:
    api_key: om-...        # ← runtime reads from here
```

**Fix after misplaced key:**
```bash
hermes config set model.api_key ""                              # clear stray
hermes config set providers.openmodel.api_key "om-..."          # put in right nest
```

## Profile Isolation Pitfall

Hermes profiles each have their own `config.yaml`. Adding OpenModel to `~/.hermes/config.yaml` (default profile) does **not** propagate to coding/youtube/traffic profiles.

**Symptom:** Coding bot still tries to use old provider, or gets 401 because provider config is missing.

**Fix:** Copy provider entry to target profile either via Python yaml script or by editing `~/.hermes/profiles/<name>/config.yaml` directly.

## Diagnostics

If 401 persists:
1. **Check key location**: `hermes config show | grep -A10 "providers:"` — verify key is inside provider block, not model block
2. **Test raw API first** — DNS may fail (OpenModel was intermittently unreachable from server IP during session, returning Cloudflare 530/1033)
3. **Test inference endpoint**, not just `/v1/models`
4. Check if key is bound to specific IP or requires email verification

## Reference

- OpenModel docs: https://docs.openmodel.ai/en
- API home: https://api.openmodel.app/v1
