# Hermes cron jobs.json structure

Hermes stores scheduled jobs per profile in:

```
~/.hermes/profiles/<profile>/cron/jobs.json
```

## Top-level shape

```json
{
  "jobs": [
    {
      "id": "96d62527e85c",
      "name": "kira-stories-morning",
      "prompt": "Опубликуй сторис для @kiraliluna.\n...",
      "skills": [],
      "skill": null,
      "model": null,
      "provider": null,
      "base_url": null,
      "script": null,
      "no_agent": false,
      "context_from": null,
      "schedule": {
        "kind": "cron",
        "expr": "0 16 * * *",
        "display": "0 16 * * *"
      },
      "schedule_display": "0 16 * * *",
      "repeat": { "times": null, "completed": 7 },
      "enabled": true,
      "state": "scheduled",
      "paused_at": null,
      "paused_reason": null,
      "created_at": "2026-06-23T22:50:04.796989+00:00",
      "next_run_at": "2026-07-01T16:00:00+00:00",
      "last_run_at": "2026-06-30T16:01:27.246776+00:00",
      "last_status": "ok",
      "last_error": null,
      "last_delivery_error": null,
      "deliver": "origin",
      "origin": { "platform": "telegram", "chat_id": "..." }
    }
  ]
}
```

## Key fields for a Bridge UI

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Short hex identifier used for `hermes cron run/pause/resume/remove <id>` |
| `name` | string | Human-readable job name |
| `prompt` | string | LLM prompt or command description |
| `script` | string \| null | Optional script path (if `no_agent: true`) |
| `schedule.kind` | string | `"cron"` or `"once"` |
| `schedule.expr` | string | Cron expression when `kind: "cron"` |
| `schedule.display` | string | Human-readable schedule, e.g. `"0 16 * * *"` or `"once at 2026-07-01 09:00"` |
| `schedule_display` | string | Fallback display string |
| `enabled` | boolean | Whether the job is enabled |
| `state` | string | `"scheduled"`, `"paused"`, etc. |
| `last_run_at` | ISO string \| null | Last execution time |
| `next_run_at` | ISO string \| null | Next scheduled execution |
| `last_status` | string \| null | e.g. `"ok"` |
| `last_error` | string \| null | Error text if last run failed |

## Important discovery rule

`hermes cron list` only enumerates jobs for the **active profile**. A Bridge UI that must show jobs across all profiles should read each profile's `cron/jobs.json` directly and attach the profile name to each record.

## Hermes CLI operations by profile

```bash
hermes --profile <profile> cron run    <job_id>
hermes --profile <profile> cron pause  <job_id>
hermes --profile <profile> cron resume <job_id>
hermes --profile <profile> cron remove <job_id>
```

The Bridge must track `profile` ownership because job IDs are not globally unique across profiles.

## Mapping to UI columns

- **Name**: `job.name || job.id`
- **Schedule**: `job.schedule.display || job.schedule.expr || job.schedule_display`
- **Status**: `enabled && state !== "paused"` → active, otherwise paused
- **Profile**: the profile directory name
- **Last run**: parse `last_run_at` as ISO timestamp
- **Next run**: parse `next_run_at` as ISO timestamp
- **Prompt preview**: truncate `prompt` to 2 lines
