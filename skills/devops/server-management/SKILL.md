---
name: server-management
description: "Monitoring, health checks, and safe server administration."
version: 1.0.0
author: Hermes Agent
---

# Server Management & Monitoring

Guidelines for maintaining server health, monitoring resources, and performing safe administration tasks.

## Resource Monitoring
Use Python and `psutil` for lightweight, non-intrusive monitoring.

### Key Metrics to Track:
1. **Disk Space:** Threshold < 10% should trigger an alert.
2. **CPU Load:** Use `psutil.cpu_percent(interval=5)` to avoid spikes. Threshold > 90% is critical.
3. **Memory (RAM):** Monitor `virtual_memory().percent`. Threshold > 90% is critical.

### Implementation Pattern (Watchdog)
Scripts should follow the "Watchdog" pattern: stay silent if everything is normal, and only output/notify when thresholds are breached.

```python
import psutil
import shutil

def check_health():
    total, used, free = shutil.disk_usage("/")
    if (free / total) < 0.1:
        print("CRITICAL: Low disk space.")
    
    if psutil.cpu_percent(interval=1) > 90:
        print("CRITICAL: High CPU usage.")
```

## Safety & Constraints
- **NO AUTONOMOUS DELETION:** Never delete files, logs, or backups automatically. Always present the findings to the user and ask for explicit permission before running any `rm` or `unlink` commands.
- **Reporting:** When problems are found, provide specific details (paths, percentages, PIDs of heavy processes).

## Automation (Cron)
Schedule monitoring tasks via the `cronjob` tool.
- Recommended interval: `every 4h` for general health, `every 30m` for high-load environments.
- Use `no_agent=True` in cron jobs for simple script-only checks to save tokens.
