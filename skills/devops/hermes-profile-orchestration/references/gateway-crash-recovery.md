# Gateway Crash Recovery — Full Walkthrough

Session: 2026-06-20
Profiles affected: default, coding, youtube, traffic
Failure: All Telegram bots silent after kill -9 on main gateway

---

## Diagnosis Flow

```bash
# 1. Check systemd status
systemctl status hermes-gateway.service
# Expected: Active or failed, logs show "killed" or "exited with status 1"

# 2. List all gateway processes
pgrep -af "hermes.*gateway"

# 3. Check machine-level lock dir
ls -la ~/.local/state/hermes/gateway-locks/
cat ~/.local/state/hermes/gateway-locks/*.lock
# Shows stale PIDs if processes were killed

# 4. Check per-profile PID files
for p in default coding youtube traffic; do
  cat ~/.hermes/profiles/$p/gateway.pid 2>/dev/null
done
```

## Recovery Commands (Copy-Paste Ready)

```bash
#!/bin/bash
set -e

PROFILES=(default coding youtube traffic)

# Step 1: Stop systemd service
systemctl stop hermes-gateway.service 2>/dev/null || true
systemctl reset-failed hermes-gateway.service 2>/dev/null || true

# Step 2: Kill all gateway processes (main + manual bg ones)
for pid in $(pgrep -f "hermes.*gateway"); do
  echo "Killing PID $pid"
  kill -9 $pid 2>/dev/null || true
done

# Step 3: Wait for death
sleep 3

# Step 4: Remove stale machine-level locks
rm -f ~/.local/state/hermes/gateway-locks/*.lock

# Step 5: Remove stale per-profile files
for profile in "${PROFILES[@]}"; do
  dir=~/.hermes/profiles/$profile
  if [[ -d "$dir" ]]; then
    rm -f "$dir/gateway.pid" "$dir/gateway.lock"
  fi
done
rm -f ~/.hermes/gateway.pid ~/.hermes/gateway.lock

# Step 6: Start main profile via systemd
systemctl start hermes-gateway.service
sleep 3
systemctl status hermes-gateway.service
```

## Manual Profile Launch (After Main Is Up)

Each additional profile needs **fully isolated environment**:

```bash
# YouTube
export HERMES_HOME=/root/.hermes/profiles/youtube
export HERMES_PROFILE=youtube
export HERMES_GATEWAY_LOCK_DIR=/tmp/locks-youtube
mkdir -p "$HERMES_GATEWAY_LOCK_DIR"
cd "$HERMES_HOME"
rm -f gateway.pid gateway.lock
nohup hermes gateway run --force >> logs/gateway-bg.log 2>&1 &

# Coding
export HERMES_HOME=/root/.hermes/profiles/coding
export HERMES_PROFILE=coding
export HERMES_GATEWAY_LOCK_DIR=/tmp/locks-coding
mkdir -p "$HERMES_GATEWAY_LOCK_DIR"
cd "$HERMES_HOME"
rm -f gateway.pid gateway.lock
nohup hermes gateway run --force >> logs/gateway-bg.log 2>&1 &
```

**Critical flags/vars explained:**

| Variable | Why Required |
|----------|--------------|
| `HERMES_HOME=<profile_dir>` | Gateway uses `HERMES_HOME/gateway.pid` for the "already running" check. Default is always `~/.hermes`, so without this, new profile sees main's PID and blocks. |
| `HERMES_PROFILE=<name>` | Loads profile-specific `.env` and `config.yaml` |
| `HERMES_GATEWAY_LOCK_DIR=/tmp/locks-<name>` | Machine-level Telegram token locks live in `<LOCK_DIR>/gateway-locks/`. Without a unique dir, `acquire_scoped_lock()` finds the other profile's lock and refuses. |
| `--force` | Bypasses the "already running under systemd" guard. Required because systemd IS running for main, and `hermes gateway run` unconditionally checks this. |

## Verification

```bash
# All running gateway PIDs
pgrep -af "gateway run"

# Should show 4 processes:
# <pid> ... hermes gateway run              (main, systemd-managed)
# <pid> ... hermes gateway run --force      (youtube)
# <pid> ... hermes gateway run --force      (coding)
# <pid> ... hermes gateway run --force      (traffic — ONLY if unique token)

# Per-profile log tails
for p in coding youtube traffic; do
  echo "==$p=="
  tail -5 ~/.hermes/profiles/$p/logs/gateway.log
done
```

## Known Traps

### Trap 1: `--force` alone is NOT enough
Without `HERMES_HOME=<profile_dir>`, even `--force` fails with:
```
Another gateway instance is already running (PID 5138).
Use 'hermes gateway run --replace' to auto-replace.
```

### Trap 2: `screen -dmS` vs `nohup`
- `screen` works but leaves parent `bash` and `SCREEN` processes visible
- `nohup` + `&` is cleaner for unattended background
- Either is fine; just don't use `bash -c '... &'` inside screen (double-shell leaks)

### Trap 3: Telegram token reuse (hardware-level lock)

If two profiles share the same `TELEGRAM_BOT_TOKEN`, the second logs:
```
Telegram bot token already in use (PID xxx). Stop the other gateway first.
```

**Root cause:** Hermes computes `SHA256(token)` and writes a machine-level lock to `~/.local/state/hermes/gateway-locks/telegram-bot-token-<sha256>.lock`. Even if you set different `HERMES_HOME` and `HERMES_GATEWAY_LOCK_DIR`, the **token hash is identical**, so `acquire_scoped_lock()` always finds the other process and refuses. This is intentional — Telegram API itself also rejects duplicate `getUpdates` polling sessions for the same token.

**Fix:** There is no workaround. You must create a **new bot via @BotFather** for every profile that needs Telegram access. Update the profile's `.env`:
```bash
TELEGRAM_BOT_TOKEN=<new_unique_token>
```

### Trap 4: systemd auto-restart during recovery

## Automation Script (Reproducible)

Save as `~/restart_hermes_profiles.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Stop main
systemctl stop hermes-gateway.service 2>/dev/null || true
systemctl reset-failed hermes-gateway.service 2>/dev/null || true

# Kill everything
for pid in $(pgrep -f "hermes.*gateway" 2>/dev/null || true); do
  kill -9 "$pid" 2>/dev/null || true
done
sleep 3

# Clean locks
rm -f ~/.local/state/hermes/gateway-locks/*.lock
for p in coding youtube traffic; do
  rm -f ~/.hermes/profiles/$p/gateway.pid ~/.hermes/profiles/$p/gateway.lock
done
rm -f ~/.hermes/gateway.pid ~/.hermes/gateway.lock

# Start main via systemd
systemctl start hermes-gateway.service
sleep 5

# Start additional profiles
launch_profile() {
  local name="$1"
  local home="/root/.hermes/profiles/$name"
  local lockdir="/tmp/locks-$name"
  mkdir -p "$lockdir"
  cd "$home"
  rm -f gateway.pid gateway.lock
  nohup bash -c "
    export HOME=/root
    export HERMES_HOME=$home
    export HERMES_PROFILE=$name
    export HERMES_GATEWAY_LOCK_DIR=$lockdir
    cd $home
    exec hermes gateway run --force >> logs/gateway-bg.log 2>&1
  " > /dev/null 2>&1 &
  echo "Launched $name (PID $!)"
}

for profile in coding youtube traffic; do
  launch_profile "$profile"
  sleep 3
done

echo "Done. Check logs:"
echo "  tail -f ~/.hermes/logs/gateway.log"
echo "  tail -f ~/.hermes/profiles/{coding,youtube,traffic}/logs/gateway.log"
```

