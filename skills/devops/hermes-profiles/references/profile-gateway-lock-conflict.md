# Profile Gateway Lock Conflict — Debug Transcript

## Symptoms

- Gateway starts, connects to Telegram (logs show `Connected to Telegram (polling mode)`), then appears to die within 7–30 seconds.
- `pgrep -f "hermes -p <profile> gateway"` returns a PID — but `ps -fp <pid>` shows DEAD or empty.
- Multiple successive start attempts produce new `.log` files each time, but the process never stays alive.
- No clear error in `errors.log`; just `SIGTERM` entries.

## Root Cause: Gateway File Lock

Hermes creates a file lock at `~/.hermes/profiles/<profile>/gateway.lock`. Only ONE process can hold it per profile. If a prior instance is zombied or the lock file is stale, new starts silently exit. If you run the gateway from a terminal with a timeout, the foreground process gets SIGTERM when the parent tool call times out, killing the gateway.

## Diagnostic Steps

```bash
# 1. Check for existing PIDs
pgrep -f "hermes -p youtube gateway"

# 2. Verify they are ACTUALLY alive
ps -fp <pid>

# 3. Check for systemd conflicts
systemctl status hermes-gateway --no-pager | head -10
# (global hermes-gateway.service runs DEFAULT profile, not youtube profile)

# 4. Inspect the lock file
cat ~/.hermes/profiles/youtube/gateway.lock

# 5. Check ALL log files, not just the newest
ls -lt ~/.hermes/profiles/youtube/logs/
tail -20 ~/.hermes/profiles/youtube/logs/gateway.log   # may belong to a DIFFERENT process
```

## Fix: Proper Detached Start

**From Python (recommended for programmatic restarts):**
```python
import subprocess, os
log = open('/root/.hermes/profiles/youtube/logs/gateway-new.log', 'wb')
proc = subprocess.Popen(
    ['/usr/local/lib/hermes-agent/venv/bin/hermes', '-p', 'youtube', 'gateway', 'run'],
    stdout=log, stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    env={**os.environ, 'HOME': '/root'},
    start_new_session=True,  # <- CRITICAL: avoids SIGHUP/SIGTERM on parent exit
    cwd='/root'
)
os.kill(proc.pid, 0)  # verify alive
```

**From bash:**
```bash
# Kill old + clear lock
pkill -9 -f "hermes -p youtube gateway"
rm -f ~/.hermes/profiles/youtube/gateway.lock
sleep 2

# Start truly detached
setsid bash -c 'hermes -p youtube gateway run > ~/.hermes/profiles/youtube/logs/gateway-$(date +%Y%m%d-%H%M%S).log 2>&1' &
```

## Timeline of Confusion from This Session

| Time | What Happened | Misleading Signal |
|------|---------------|-------------------|
| 13:52 | Gateway started, connected to Telegram | Log says `Connected` — looks healthy |
| 13:52:21 | Got SIGTERM from systemd | Parent PID=1, systemd context |
| 13:58 | New start attempt (screen) | PID 1484 created but died quickly |
| 14:00 | Third start attempt | PID 1637 created but also died |
| 14:01 | Realization: systemd hermes-gateway.service was RUNNING (PID 987) — but for default profile, not youtube | None of the youtube starts could hold the lock |

## Key Lesson

- **Never start `hermes -p <profile> gateway run` as a foreground command** inside a tool call with a timeout — it WILL get SIGTERM when the tool timeout expires.
- **Always use `start_new_session=True`** (or `setsid`) when launching from code.
- **Clear `gateway.lock` before restarting** after a suspected lock hang.
