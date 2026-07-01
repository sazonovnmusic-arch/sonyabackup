---
name: cronjob-operations
description: |
  Diagnose, inspect, and safely restart Hermes cron jobs. Covers status checks,
  log inspection, output file analysis, and recovery patterns for failed
  scheduled tasks.
category: devops
---

# Cron Job Operations

## When to Use

- User asks "why didn't my cron job run" or "is my cron job working"
- A scheduled task shows `last_status: error`
- User requests a manual rerun of a cron job
- Need to verify whether a long-running cron task is still active

## Workflow

### 1. Inspect Status
```
cronjob action=list
```
Check:
- `last_status`: `ok` | `error`
- `last_run_at`: when it last fired
- `next_run_at`: when it is due next
- `enabled`: true/false
- `state`: `scheduled` | `running` | `paused`

### 2. Inspect Output Files
```
ls -lt ~/.hermes/cron/output/<job_id>/
```
- Compare file sizes: a tiny file (e.g. < 6 KB) often means the job failed early.
- Compare timestamps: if the latest file matches `last_run_at`, the job at least started.

### 3. Inspect Logs (Critical Before Rerun)
Check **both** logs:
```
tail -50 ~/.hermes/logs/agent.log  | grep -i "<job_id>"
tail -50 ~/.hermes/logs/errors.log | grep -i "<job_id>"
```

Look for:
- `already running — skipping` → the job is still in progress; **do not rerun**
- `Connection error` from the API provider → transient network issue; rerun usually fixes it
- Browser tool activity (`browser_navigate`, `browser_click`) → the job is actively working; be patient

### 4. Read the Output File
```
read_file path=~/.hermes/cron/output/<job_id>/<latest>.md
```
The file usually contains the error message or the final report.

### 5. Safe Rerun Decision
| Scenario | Action |
|---|---|
| `last_status: error`, no "already running" in logs, output file is tiny | `cronjob action=run job_id=...` |
| Logs show "already running — skipping" | Wait; the job is active |
| Browser-heavy job, output file not yet present (< 5 min after run) | Wait 5–15 min before concluding failure |
| Recurring `Connection error` at same time daily | Check provider/API health; consider rescheduling to a different hour |

## Pitfalls

- **Do not chain multiple `cronjob run` calls.** If the scheduler says `already running`, every subsequent run is silently skipped. It only wastes time.
- **Do not judge success by file absence in the first 2 minutes.** Browser-based tasks (e.g. scraping 20 vacancies) take 5–15 min to complete.
- **`Connection error` from the LLM provider ≠ a bug in the job logic.** It is a transient API/network failure. A single retry is usually sufficient.
- **If a job failed at 06:00 and the user asks for a rerun at 07:15**, check logs first — the scheduler may already be executing the rerun you triggered earlier.

## References

- `references/cron-log-patterns.md` — annotated log snippets and error signatures
