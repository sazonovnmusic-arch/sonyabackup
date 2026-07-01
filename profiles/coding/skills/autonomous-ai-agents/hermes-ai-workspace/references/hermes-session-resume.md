# Creating Hermes sessions from a Bridge API so `--resume` works

When a web dashboard (AI Workspace) needs to start a new chat with a Hermes agent, the cleanest approach is:

1. Insert a new row into the target profile's `state.db` `sessions` table.
2. Populate the fields Hermes CLI expects.
3. Keep the session empty (no messages).
4. Invoke `hermes --profile <name> chat -q <msg> --resume <session_id>`.

## Why this matters

If you insert only `id`, `source`, `started_at`, `title`, and leave everything else `NULL`, Hermes will print:

```
Session not found: <session_id>
Use a session ID from a previous CLI run.
```

It will not process the message and no assistant reply is written.

## Minimal working insert

```python
import sqlite3, time

conn = sqlite3.connect('/root/.hermes/profiles/<name>/state.db')

system_prompt = """# Hermes Agent Persona

You are a helpful Hermes agent."""

now = time.time()
conn.execute(
    """
    INSERT INTO sessions (
        id, source, user_id, model, system_prompt, started_at, ended_at,
        message_count, billing_provider, billing_base_url, estimated_cost_usd,
        cost_status, cost_source, title, archived
    ) VALUES (?, 'api', '', ?, ?, ?, ?, 0, ?, ?, 0.0, 'unknown', 'none', ?, 0)
    """,
    (
        session_id,
        model,                  # e.g. 'kimi-k2.7-code'
        system_prompt,
        now,
        now,
        provider,               # e.g. 'ollama-cloud'
        base_url,               # e.g. 'https://ollama.com/v1'
        title,
    ),
)
conn.commit()
```

Read the values from the profile's `config.yaml`:

```python
model = cfg.get('model', {}).get('default')
provider = cfg.get('model', {}).get('provider')
base_url = cfg.get('providers', {}).get(provider, {}).get('base_url')
if not base_url:
    base_url = cfg.get('model', {}).get('base_url')
```

## Sending the first message

Do **not** manually insert the `user` message first. Run:

```bash
hermes --profile <name> chat -q "Привет" --resume <session_id> --source api
```

Hermes will:
- write the user message,
- call the LLM,
- write the assistant message.

## Duplicate check

If a session already contains a `user` message and you run `hermes chat -q --resume`, Hermes may add a second user message with the same content. Always resume into an empty session for the first Bridge message.

## Useful queries

```sql
-- latest sessions for a profile
SELECT id, title, started_at, message_count
FROM sessions
WHERE source = 'api' AND archived = 0
ORDER BY started_at DESC;

-- messages in a session
SELECT id, role, content, timestamp
FROM messages
WHERE session_id = ? AND active = 1
ORDER BY timestamp ASC;
```
