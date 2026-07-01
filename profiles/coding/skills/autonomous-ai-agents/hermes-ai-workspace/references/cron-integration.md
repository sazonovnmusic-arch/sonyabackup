# Cron integration in AI Workspace

## Where cron jobs live

Hermes has a built-in scheduler exposed via `hermes cron`. Jobs are stored per profile under:

```
~/.hermes/profiles/<name>/cron/jobs.json
```

**Important:** `hermes cron list` only returns jobs for the currently active Hermes profile. The Bridge must read `jobs.json` directly for every discovered profile to show all cron jobs. See `references/cron-jobs-json-parser.md` for the exact parser.

## Why a separate Cron tab (not Kanban)

Cron jobs are **recurring automation triggers**, not one-off tasks. They belong in a dedicated tab. A cron job can **spawn** a Kanban card on each tick, but should not itself appear as a board card.

## Bridge API wrapper

Run Hermes CLI as subprocess. Note that `hermes cron list --json` may not exist in all versions; in Hermes 0.16.0 it returns plain text. Prefer the human-readable `list` output and parse it, or read `~/.hermes/profiles/<name>/cron/jobs.json` directly.

```python
def _cron_cli(*args, profile: str | None = None):
    cmd = ["hermes"]
    if profile:
        cmd += ["--profile", profile]
    cmd += ["cron"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

# Example: list for a single profile
def list_cron_jobs_for_profile(profile: str):
    # Try JSON flag first; fall back to plain text.
    res = _cron_cli("list", "--json", profile=profile)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout)
        except json.JSONDecodeError:
            pass
    res = _cron_cli("list", profile=profile)
    return _parse_cron_text(res.stdout)
```

Routes:

```
GET    /api/cron              # list jobs across all profiles by parsing jobs.json
POST   /api/cron              # create: hermes cron create --name --schedule --prompt
POST   /api/cron/{id}/run     # hermes cron run <id>
POST   /api/cron/{id}/pause   # hermes cron pause <id>
POST   /api/cron/{id}/resume  # hermes cron resume <id>
DELETE /api/cron/{id}         # hermes cron remove <id>
POST   /api/cron/{id}/tasks   # create a Kanban task from this cron job
```

## Parsing jobs.json

```python
import yaml
from pathlib import Path

cron_file = profile_path / "cron" / "jobs.json"
if cron_file.exists():
    data = yaml.safe_load(cron_file.read_text(encoding="utf-8")) or {}
    for job_id, job in data.items():
        if not isinstance(job, dict):
            continue
        yield {
            "id": job_id,
            "name": job.get("name") or job_id,
            "schedule": job.get("schedule"),
            "prompt": job.get("prompt") or job.get("command") or job.get("script"),
            "enabled": not job.get("paused", False),
            "last_run": job.get("last_run"),
            "next_run": job.get("next_run"),
            "profile": profile.name,
        }
```

## Creating a Kanban task from a cron job

```python
@app.post("/api/cron/{job_id}/tasks")
def create_task_from_cron(job_id: str) -> Task:
    jobs = list_cron_jobs()
    job = next((j for j in jobs if j.id == job_id), None)
    if not job:
        raise HTTPException(404, "Cron job not found")
    title = f"[Cron] {job.name or job_id}"
    description = f"Schedule: {job.schedule}\nPrompt: {job.prompt or ''}"
    # insert into workspace.db tasks table
    ...
```

## UI tab contents

- Form: name, schedule, profile select, prompt.
- Job list with actions: Run, Pause/Resume, Delete, "В Kanban".
- Status badge: active / paused.

## Future extensions

- Show last/next run timestamps.
- Link each cron-spawned task back to the cron job that created it (store `cronjob_id` in `tasks`).
- Enable cron job to auto-create tasks on every tick via a wrapper prompt.
