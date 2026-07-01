# Multi-Profile Gateway Diagnostics

Session: 2026-06-20 — all 4 Telegram bots went silent after `kill -9` killed the main gateway.

## Symptom

All bots dead. Main gateway systemd service stuck in `failed`. Manual restart attempts fail with:

```
Telegram bot token already in use (PID 4004). Stop the other gateway first.
```

or

```
A gateway is already running under systemd (system) for this profile.
```

## Root Causes

### 1. Zombie lock files
`kill -9` leaves stale scoped locks in:
```
~/.local/state/hermes/gateway-locks/
```

Format: `<scope>-<hash>.lock`, e.g. `telegram-bot-token-198c4e3602acdaea.lock`

Each lock stores PID + start_time. If the PID is dead but the file remains, new gateway instances see it and refuse to start.

### 2. Stale PID files
```
~/.hermes/profiles/*/gateway.pid
~/.hermes/gateway.pid
~/.hermes/profiles/*/gateway.lock
```

These are used by `hermes gateway run` to detect concurrent instances. If left behind after SIGKILL, they also block startup.

### 3. Gateway thinks systemd owns everything
`hermes gateway run` detects if a systemd service supervises the current HERMES_PROFILE. Detection logic checks systemd cgroup membership, which can trigger even for unrelated profiles if the main service is running.

### 4. Duplicate bot tokens across profiles
In this session, `traffic` profile had the SAME TELEGRAM_BOT_TOKEN as `main` profile (both = ***). This means they can never run simultaneously — Telegram rejects duplicate polling connections with identical tokens.

## Fix Procedure

### Step 1: Stop all gateway processes
```bash
systemctl stop hermes-gateway.service
for pid in $(pgrep -f "hermes.*gateway"); do kill -9 $pid 2>/dev/null; done
sleep 2
pgrep -f "hermes.*gateway" || echo "all dead"
```

### Step 2: Remove stale locks
```bash
rm -f ~/.local/state/hermes/gateway-locks/*.lock
rm -f ~/.hermes/gateway.pid ~/.hermes/gateway.lock
rm -f ~/.hermes/profiles/*/gateway.pid ~/.hermes/profiles/*/gateway.lock
```

### Step 3: Verify unique tokens per profile
```bash
for p in main coding youtube traffic; do
    f="$HOME/.hermes/profiles/$p/.env"
    [ -f "$f" ] || f="$HOME/.hermes/.env"
    echo "==$p=="
    grep "TELEGRAM_BOT_TOKEN" "$f" 2>/dev/null | sed 's/TELEGRAM_BOT_TOKEN=/BOT: /'
done
```

If any two profiles share the same token value, one must change. Request a new token from @BotFather.

### Step 4: Restart main gateway via systemd
```bash
systemctl reset-failed hermes-gateway.service
systemctl start hermes-gateway.service
systemctl status hermes-gateway.service --no-pager
```

### Step 5: Start additional profiles
Option A — foreground with --force (good for debugging):
```bash
cd ~/.hermes/profiles/youtube
HERMES_PROFILE=youtube hermes gateway run --force
```

Option B — wrap in systemd service units (best for production, requires root):
Create `/etc/systemd/system/hermes-gateway-youtube.service` with:
- `ExecStart=/usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli.main gateway run`
- `WorkingDirectory=/root/.hermes/profiles/youtube`
- `Environment="HERMES_PROFILE=youtube"`
- `Restart=always`

Then:
```bash
systemctl daemon-reload
systemctl enable hermes-gateway-youtube.service
systemctl start hermes-gateway-youtube.service
```

Repeat for coding, traffic (with unique tokens).

## Verification

```bash
# Active locks
ls ~/.local/state/hermes/gateway-locks/

# Running processes
ps aux | grep "hermes.*gateway"

# Per-profile connectivity (bot info)
for p in main coding youtube traffic; do
    f="$HOME/.hermes/profiles/$p/.env"
    [ -f "$f" ] || f="$HOME/.hermes/.env"
    tk=$(grep "^TELEGRAM_BOT_TOKEN" "$f" 2>/dev/null | sed 's/.*=//')
    [ -z "$tk" ] && continue
    curl -s "https://api.telegram.org/bot${tk}/getMe" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["result"]["username"] if d.get("ok") else d)'
done
```

## Prevention

1. **Never use `kill -9`** on gateway unless absolutely necessary. Use `systemctl stop hermes-gateway.service` or graceful Ctrl+C.
2. **One bot = one token**. Never reuse tokens across profiles.
3. **Use systemd per profile** for auto-restart on crash.
4. **Monitor lock directory age**: old lock files with dead PIDs are a red flag.

## Key Files / Dirs

| Path | Purpose |
|------|---------|
| `~/.local/state/hermes/gateway-locks/` | Scoped machine-local locks (token conflicts) |
| `~/.hermes/gateway.pid` | Main gateway PID file |
| `~/.hermes/gateway.lock` | Main gateway lock file |
| `~/.hermes/profiles/<name>/gateway.pid` | Per-profile PID |
| `~/.hermes/profiles/<name>/gateway.lock` | Per-profile lock |
| `~/.hermes/profiles/<name>/logs/gateway.log` | Runtime logs |
| `/etc/systemd/system/hermes-gateway*.service` | Service definitions |
