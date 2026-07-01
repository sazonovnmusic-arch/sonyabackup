# Silent Telegram Bot Failure — Diagnosis Recipe

**Class:** default-profile gateway loses Telegram connectivity without crashing.
**Trigger:** `TELEGRAM_BOT_TOKEN` disappears from `~/.hermes/.env` (overwrite, manual edit, migration).
**Symptom:** Bot is "dead" — no responses in Telegram, but systemd service shows `active (running)` and no errors in `journalctl`.

---

## Diagnostic Sequence (copy-paste ready)

### 1. Check running services
```bash
systemctl list-units --type=service --state=running | grep hermes
```
Expected: `hermes-gateway.service loaded active running`

### 2. Check ALL units (including failed)
```bash
systemctl list-units --all --type=service | grep hermes
```
Note: `hermes-gateway-default.service` may not exist — default often runs as bare `hermes-gateway.service`.

### 3. Check connected platforms in gateway log
```bash
tail -30 ~/.hermes/logs/gateway.log
# OR
journalctl -u hermes-gateway -n 30 --no-pager
```
**Red flag:** `Gateway running with 1 platform(s)` — means ONLY api_server is connected, Telegram is absent.
Healthy startup should say: `Connecting to telegram...` then `✓ telegram connected`.

### 4. Verify .env contains the token
```bash
grep "TELEGRAM_BOT_TOKEN" ~/.hermes/.env
```
If empty → token was lost. Check `.env` mtime:
```bash
stat ~/.hermes/.env
```
Compare with when bot "went silent". Overwrite date = likely culprit.

### 5. Verify config.yaml still enables telegram platform
```bash
grep -A 2 "^telegram:" ~/.hermes/config.yaml
```
Should show platform adapter reference, not be empty.

### 6. Verify no allowlist is blocking the user
If token exists but bot still ignores you:
```bash
grep -i "ALLOW" ~/.hermes/.env
```
Look for `GATEWAY_ALLOW_ALL_USERS=true` or `TELEGRAM_ALLOWED_USERS=<your_id>`.
Default after a fresh `.env` write: no allowlists configured → ALL unauthorized users denied.

---

## Root Causes Found in Practice

| Cause | Evidence | Fix |
|---|---|---|
| `.env` overwritten, token removed | `stat .env` shows recent mtime, `grep TOKEN` empty | Restore token from backup/other profile/botfather |
| No `TELEGRAM_BOT_TOKEN` env var passed into systemd unit | `cat /proc/<pid>/environ` lacks TOKEN | Add `Environment=TELEGRAM_BOT_TOKEN=...` to unit OR use `.env` file |
| Stale gateway lock after crash | `gateway.lock` exists but no PID | `rm -f ~/.hermes/gateway.lock ~/.hermes/gateway.pid` |
| Allowlist denial | Log says `All unauthorized users will be denied` | Add `GATEWAY_ALLOW_ALL_USERS=true` to `.env` |

---

## Token Recovery (when no backup exists)

```bash
# 1. Check if token is in any backup config
find ~/.hermes -name ".env*" -o -name "config.yaml.bak*" | xargs grep -h "TELEGRAM_BOT_TOKEN" 2>/dev/null | head -5

# 2. Check if token is in old logs (may be redacted, but worth a shot)
grep -oE 'TELEGRAM_BOT_TOKEN=[0-9]{8,10}:[A-Za-z0-9_-]{30,50}' ~/.hermes/logs/*.log 2>/dev/null

# 3. Check other profiles for the SAME token (collision indicator)
grep "TELEGRAM_BOT_TOKEN" ~/.hermes/profiles/*/.env 2>/dev/null

# 4. Last resort: message @BotFather → /mybots → select bot → API Token
```

---

## Prevention

- Keep `.env` backups: `cp ~/.hermes/.env ~/.hermes/.env.bak.$(date +%Y%m%d_%H%M%S)` before any manual edit.
- Track `.env` in a private dotfiles repo (encrypt secrets with `git-crypt` or `sops`).
- When regenerating `.env` from a template, append — never blindly overwrite.
