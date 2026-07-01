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

## Safe disk cleanup for development servers

Before installing large packages (Electron apps, Rust toolchains, ML models) on a small VPS, check disk and RAM:

```bash
free -h && df -h / && nproc
```

Common safe-to-delete caches that free large amounts of space:

| Path | Typical size | Safe? | Notes |
| --- | --- | --- | --- |
| `/root/.cache/ms-playwright` | 1–2 GB | ✅ Yes | Playwright browser cache, re-downloaded on demand. |
| `/root/.npm/_cacache` | 300–800 MB | ✅ Yes | npm package cache, rebuilt automatically. |
| `/root/.cache/pip` | 100 MB+ | ✅ Yes | pip wheel cache. |
| `/opt/<project>/node_modules` | 1–2 GB | ✅ Usually | Can reinstall with `npm install`; delete only if you are switching to a packaged build (`.deb`, AppImage). |
| `/opt/<project>/.git` | 500 MB–1 GB | ✅ Yes | Source history; not needed for running a packaged app. |
| `~/.hermes/profiles/*` | varies | ❌ NEVER | Hermes profiles and their `state.db`/cron configs. Delete only with explicit user permission. |
| `~/ai-workspace-archive/*` | varies | ❌ Usually no | Project archives and restore instructions the user asked to keep. |

After cleanup, always verify space:

```bash
df -h /
```

## Safety & Constraints
- **NO AUTONOMOUS DELETION:** Never delete files, logs, or backups automatically. Always present the findings to the user and ask for explicit permission before running any `rm` or `unlink` commands.
- **NEVER delete Hermes profiles, `state.db`, cron configs, or skills** without explicit user permission. They contain live configuration and chat history.
- **NEVER delete archives the user explicitly asked to keep** (e.g., `ai-workspace-archive`) without confirmation.
- **Reporting:** When problems are found, provide specific details (paths, percentages, PIDs of heavy processes).

## Automation (Cron)
Schedule monitoring tasks via the `cronjob` tool.
- Recommended interval: `every 4h` for general health, `every 30m` for high-load environments.
- Use `no_agent=True` in cron jobs for simple script-only checks to save tokens.
