# Recipe: insert a Hermes-resumable session from Bridge

Use when the Bridge API must create a new chat session that `hermes chat --resume SESSION_ID` will accept.

## Minimal required columns

```python
import sqlite3, time, uuid
from datetime import datetime, timezone

session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
now = time.time()

conn.execute("""
    INSERT INTO sessions (
        id, source, user_id, model, system_prompt, started_at, ended_at,
        message_count, billing_provider, billing_base_url, estimated_cost_usd,
        cost_status, cost_source, title, archived
    )
    VALUES (?, 'api', '', ?, ?, ?, ?, 0, ?, ?, 0.0, 'unknown', 'none', ?, 0)
""", (
    session_id,
    model,                       # e.g. profile_config['model']['default']
    system_prompt,               # e.g. '# Hermes Agent Persona\\n\\nYou are a helpful agent.'
    now,
    now,
    provider,                    # e.g. 'ollama-cloud'
    base_url,                    # e.g. 'https://ollama.com/v1'
    title,
))
conn.commit()
```

## Check that it is resumable

```bash
hermes --profile <profile> chat -q "ping" --resume <session_id> --source api
```

Expected: Hermes prints a response, and `state.db` now contains one `user` and one `assistant` row for that session.

## If `--resume` says "Session not found"

1. Verify `id` format matches Hermes convention (`YYYYMMDD_HHMMSS_hex`).
2. Verify `model` is non-empty.
3. Verify `billing_provider` and `billing_base_url` match the profile's active provider.
4. Verify the row was inserted into the **correct profile's** `state.db`, not the default/root one.

## Anti-pattern

Do **not** pre-insert a `user` row before calling `hermes chat --resume`. Hermes will insert its own user row, causing duplication.
