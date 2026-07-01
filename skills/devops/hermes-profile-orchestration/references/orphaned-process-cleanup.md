# Orphaned Background Process Cleanup After Gateway Restart

When Hermes agents start background processes via `terminal(background=true)` (e.g., `webhook_server.py`, `cloudflared`, custom scripts), those processes are NOT children of the gateway process. When systemd restarts the gateway, only the main gateway PID is killed — orphaned background processes survive.

## Problem

- **Memory leak:** Old webhook/cloudflared instances keep consuming RAM
- **Port conflicts:** New instances can't bind to already-used ports
- **Zombie connections:** Old Telegram/webhook listeners interfere with new ones
- **Silent accumulation:** Each restart adds more orphans until the server is bloated

## How to Detect

```bash
# Check all matching processes and their cgroups
for pid in $(pgrep -f "webhook_server\|cloudflared"); do
  cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
  cgroup=$(cat /proc/$pid/cgroup 2>/dev/null | grep systemd | head -1)
  echo "PID=$pid CMD='$cmd'"
  echo "  CGROUP=$cgroup"
  if echo "$cgroup" | grep -q "hermes-gateway"; then
    echo "  → Under systemd — OK"
  else
    echo "  → ORPHANED — should be killed"
  fi
  echo
done
```

**Typical orphaned output:**
```
PID=88361 CMD='python3 /root/.hermes/profiles/instamodel/webhook_server.py'
  CGROUP=1:freezer:/
  → ORPHANED — should be killed
```

## One-Shot Cleanup Script

```bash
#!/bin/bash
# cleanup_orphans.sh — run after gateway restart

for pid in $(pgrep -f "webhook_server\|cloudflared" 2>/dev/null); do
  cgroup=$(cat /proc/$pid/cgroup 2>/dev/null | grep systemd | head -1)
  if ! echo "$cgroup" | grep -q "hermes-gateway"; then
    echo "Killing orphaned PID $pid (cmd: $(cat /proc/$pid/cmdline | tr '\0' ' '))"
    kill -9 "$pid" 2>/dev/null
  fi
done
```

## Prevention: ExecStopPost in Systemd Unit

Add to the service file:

```ini
[Service]
ExecStopPost=/bin/sh -c 'for pid in $(pgrep -f "webhook_server\|cloudflared"); do if ! cat /proc/$pid/cgroup 2>/dev/null | grep -q "hermes-gateway"; then kill -9 $pid 2>/dev/null; fi; done'
```

This runs after `ExecStop` (gateway termination) and kills any orphaned children that escaped the cgroup.

## Prevention: systemd Slice + Scope

For background processes that MUST survive gateway restart, move them to a separate systemd scope:

```bash
# Start webhook_server under its own systemd scope (survives gateway restarts)
systemd-run --scope --unit=instamodel-webhook \
  python3 /root/.hermes/profiles/instamodel/webhook_server.py
```

Then manage it independently:
```bash
systemctl status instamodel-webhook.scope
systemctl stop instamodel-webhook.scope
```

## Prevention: PID File Tracking

Have the background script write its PID to a known file, then clean it on restart:

```python
# In webhook_server.py
import os
pid_file = "/tmp/instamodel_webhook.pid"
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))
```

Then in restart script:
```bash
if [ -f /tmp/instamodel_webhook.pid ]; then
  kill -9 $(cat /tmp/instamodel_webhook.pid) 2>/dev/null
  rm -f /tmp/instamodel_webhook.pid
fi
```

## Recommended Pattern

For most use cases, **ExecStopPost cleanup** is the simplest and most reliable. For processes that need to outlive the gateway (e.g., persistent webhook listeners), use a **separate systemd service** instead of `terminal(background=true)`.

## Verification After Cleanup

```bash
# Should show nothing (or only processes under systemd cgroups)
for pid in $(pgrep -f "webhook_server\|cloudflared"); do
  cat /proc/$pid/cgroup 2>/dev/null | grep systemd | head -1
done
```
