# Cron Log Patterns & Error Signatures

## Pattern: `already running — skipping`

**Log snippet:**
```
2026-06-24 07:20:52,767 INFO cron.scheduler: Job 'hh-vacancy-search' already running — skipping
```

**Meaning:** The scheduler received a `cronjob run` command but the same job is still executing from an earlier trigger. **Action:** wait; do not retry.

**Root cause in this session:** First manual rerun at 07:15 started a browser-heavy task. A second `run` at 07:20 was silently skipped. The job completed on its own ~10 min later.

---

## Pattern: `Connection error.` (API provider)

**Log snippet:**
```
2026-06-24 06:00:20,745 WARNING ... API call failed (attempt 1/3) error_type=APIConnectionError ... summary=Connection error.
... retries exhausted ...
2026-06-24 06:00:43,091 ERROR cron.scheduler: Job 'hh-vacancy-search' failed: RuntimeError: Connection error.
```

**Meaning:** The LLM provider (here `ollama-cloud`) could not be reached. This is a **transient network/API failure**, not a bug in the job logic.

**Action:** One manual rerun (`cronjob run`) is usually enough. If it recurs at the same time daily, investigate provider health or reschedule the job to a different hour.

---

## Pattern: Browser-tool activity mid-run

**Log snippet:**
```
... tool browser_navigate completed (3.46s, 8668 chars)
... tool browser_click completed (0.32s, 36 chars)
... tool browser_snapshot completed (0.62s, 8440 chars)
```

**Meaning:** The cron agent is actively navigating and scraping. **Action:** be patient. Browser-heavy tasks (e.g. 20 vacancy scrapes) take 5–15 min. File absence in the first 2 minutes is normal.

---

## Reference: Output file size heuristic

| Size | Typical meaning |
|---|---|
| < 6 KB | Job failed early; often contains only the prompt + error line |
| 10–30 KB | Successful completion with content (e.g. 20 vacancies + cover letters) |
| > 50 KB | Large output; likely ok |

**Example from session:**
- Failed run: 5,012 bytes (`2026-06-24_06-00-43.md`)
- Successful run: 29,276 bytes (`2026-06-23_06-04-20.md`)
