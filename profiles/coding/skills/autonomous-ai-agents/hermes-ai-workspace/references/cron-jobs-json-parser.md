# Reading Hermes cron jobs from jobs.json

## Why not `hermes cron list`

`hermes cron list` (with or without `--json`) returns jobs only for the **currently active Hermes profile** (the one implied by `HERMES_HOME` or `--profile`). If the Bridge process inherits an active profile such as `coding`, it will not see cron jobs owned by `youtube`, `instamodel`, `default`, etc.

Hermes stores the actual scheduler state per profile in:

```
~/.hermes/profiles/<profile>/cron/jobs.json
```

The Bridge must read these files directly for every discovered profile.

## File structure

```json
{
  "jobs": [
    {
      "id": "54bb7f5a09d5",
      "name": "Weekly trend scout",
      "prompt": "...",
      "schedule": {
        "kind": "cron",
        "expr": "30 5 * * 1",
        "display": "30 5 * * 1"
      },
      "schedule_display": "30 5 * * 1",
      "enabled": true,
      "state": "scheduled",
      "last_run_at": "2026-06-29T03:00:00+00:00",
      "next_run_at": "2026-07-06T03:00:00+00:00"
    }
  ]
}
```

Important fields:
- `id` — stable job identifier, used for pause/resume/run/remove.
- `name` — human-readable name.
- `prompt` — text prompt given to the agent when the job fires.
- `schedule.expr` or `schedule.display` — cron expression.
- `enabled` and `state` — active/paused state.
- `last_run_at`, `next_run_at` — ISO timestamps.

## Bridge parser (FastAPI)

```python
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

def _parse_iso(value: Any) -> float | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return None

def list_cron_jobs(profile: str | None = None):
    jobs = []
    profiles = [p for p in read_profiles() if profile is None or p.name == profile]
    for p in profiles:
        cron_file = profile_path(p.name) / "cron" / "jobs.json"
        if not cron_file.exists():
            continue
        try:
            data = json.loads(cron_file.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        for job in data.get("jobs", []):
            if not isinstance(job, dict):
                continue
            sched = job.get("schedule", {}) or {}
            jobs.append({
                "id": job.get("id") or str(uuid.uuid4())[:12],
                "name": job.get("name") or "Unnamed job",
                "schedule": sched.get("display") or sched.get("expr") or job.get("schedule_display"),
                "prompt": job.get("prompt") or job.get("script") or "",
                "enabled": job.get("enabled", True) and job.get("state") != "paused",
                "last_run": _parse_iso(job.get("last_run_at")),
                "next_run": _parse_iso(job.get("next_run_at")),
                "profile": p.name,
            })
    return jobs
```

## Control endpoints

Use the discovered `profile` field to route `hermes cron` commands to the owning profile:

```python
@app.post("/api/cron/{job_id}/run")
def run_cron_job(job_id: str):
    for job in list_cron_jobs():
        if job["id"] == job_id:
            result = subprocess.run(
                ["hermes", "--profile", job["profile"], "cron", "run", job_id],
                capture_output=True, text=True, timeout=60
            )
            return {"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    raise HTTPException(404, "Cron job not found")
```

Same pattern for `pause`, `resume`, `remove`.

## Pitfall: stale state after control action

`hermes cron pause/resume` updates `jobs.json` but the Bridge may cache the list. Always re-read the JSON after a mutation before returning to the UI.

## See also

- `references/cron-integration.md` — broader Cron tab design and Kanban spawning.
