---
name: server-monitoring-and-automation
description: "Setup and manage autonomous server health monitoring, watchdogs, and resource tracking."
version: 1.0.0
author: Hermes
license: MIT
---

# Server Monitoring and Automation

This skill covers the creation and management of autonomous monitoring systems (watchdogs) that track server resources (CPU, RAM, Disk) and notify the user of critical states via cron jobs.

## Trigger Conditions
- User wants to "monitor" or "track" server health.
- Requests for alerts on low disk space or high CPU/RAM usage.
- Need for a background "technical manager" for the server.

## Steps

### 1. Create the Monitoring Script
Create a Python script (e.g., `~/.hermes/scripts/monitor.py`) using `psutil` and `shutil` for resource gathering. 

**Standard Checks:**
- **Disk:** Threshold 10% free.
- **CPU:** Threshold 90% usage (sampled over an interval).
- **RAM:** Threshold 90% usage.

### 2. Implementation Pattern (Watchdog)
Use the **Watchdog Pattern**: The script should only produce output when an issue is detected. If everything is healthy, it stays silent. This minimizes notification noise and token usage.

### 3. Schedule via Cron
Create a `cronjob` with `no_agent=True`. This ensures the script's output is delivered directly to the user as a message without extra reasoning overhead.

```bash
# Example cron creation
cronjob(action='create', name='Server Watchdog', schedule='every 4h', script='monitor.py', no_agent=True)
```

## Pitfalls & Constraints
- **Safety First:** Monitoring scripts MUST NOT perform destructive actions (like `rm` or `git clean`) without explicit interactive user approval.
- **Environment:** Always check for `psutil` availability (`pip install psutil`).
- **Pathing:** Use filename only in `cronjob(script=...)` calls; the script must reside in `~/.hermes/scripts/`.

## References
- `references/resource-monitor-script.py`: A known-good monitoring script implementation.
