---
name: server-monitoring
description: "Set up autonomous server health monitoring using Python scripts and cron jobs."
version: 1.0.0
author: Hermes Agent
---

# Server Monitoring & Watchdogs

This skill covers setting up a lightweight, autonomous "technical manager" to monitor server health (disk space, CPU load, RAM, etc.) and alert the user when thresholds are breached.

## Workflow

1.  **Define Thresholds:** Identify critical limits (e.g., <10% disk free, >90% CPU load).
2.  **Create Monitor Script:** Write a Python script using `psutil` or `shutil` and save it to `~/.hermes/scripts/`.
    -   *Pattern:* The script should be "silent" if everything is OK (watchdog pattern) to minimize noise and token usage.
    -   *Safety:* Explicitly exclude any file deletion or destructive actions from the script logic.
3.  **Test Locally:** Run the script once via `terminal` to verify output and permissions.
4.  **Schedule via Cron:** Use the `cronjob` tool to run the script at a regular interval.
    -   Set `no_agent: true` for pure script-based watchdogs to maximize efficiency.
    -   Ensure the `prompt` explicitly reminds the agent that destructive actions are forbidden.

## Tool Quirk: Cron Job Script Paths
When creating a `cronjob` with the `script` parameter:
- **Do NOT use absolute paths** (e.g., `/root/.hermes/scripts/foo.py`).
- **USE relative paths** from the scripts directory (e.g., `foo.py`). The script must be located in `~/.hermes/scripts/`.

## Verification Steps
- List active jobs with `hermes cron list` or the `cronjob(action='list')` tool.
- Check the last run status to ensure the script executes correctly.

## Pitfalls
- **Token Waste:** Running heavy models for simple health checks is inefficient. Always prefer "Flash" or "Mini" models for the watchdog role.
- **Permission Denied:** Ensure the environment has the necessary permissions to read system stats (usually standard for `psutil`).
- **Destructive Autonomy:** Never give a watchdog the power to `rm` or `git reset` without a human in the loop.
