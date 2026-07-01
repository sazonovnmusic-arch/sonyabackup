# Race-safe chat delivery (SSE / WebSocket)

Reference: how to make live chat delivery reliable when the backend (Hermes CLI) can finish before the frontend has opened its SSE/WebSocket connection, and how to recover when a push is missed.

## The problem

In the AI Workspace architecture the Bridge invokes `hermes chat --resume <session>` in a background thread. On a fast model or a short answer the CLI can return and write the assistant message to `state.db` **before** the React UI has finished:

1. creating a new session,
2. updating `activeSessionId`,
3. running the `useEffect` that opens `EventSource` / `WebSocket`.

When that happens the server pushes the message to zero connected clients. The UI shows the typing indicator forever, and a page refresh reveals the message was already saved. This is a race condition, not a model failure.

## Server-side fixes

### 1. Capture the main event loop on startup

Hermes uses its own event loop inside the background thread. If the Bridge tries to call `asyncio.run(_notify_all(...))` from that thread it will fail because a loop is already running. Capture uvicorn's main loop once and schedule the coroutine on it:

```python
import asyncio

_main_loop: asyncio.AbstractEventLoop | None = None

@app.on_event("startup")
def _store_main_loop():
    global _main_loop
    try:
        _main_loop = asyncio.get_running_loop()
    except RuntimeError:
        _main_loop = None

def _notify_from_thread(session_key: str, payload: dict):
    print(f"[notify-from-thread] session={session_key} payload={payload.get('id')} loop={_main_loop}")
    if _main_loop and _main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(_notify_all(session_key, payload), _main_loop)
        except Exception as e:
            print(f"[notify] threadsafe failed: {e}")
    else:
        try:
            asyncio.run(_notify_all(session_key, payload))
        except Exception as e:
            print(f"[notify] fallback failed: {e}")
```

### 2. Retry notify until a client connects

After the first push, keep retrying a few times with increasing delay. If the UI connects during the retry window it will receive the message:

```python
def _run_hermes_task(task_id, profile, session_id, cmd):
    # ... run hermes, read/write fallback message, get assistant_id and content ...

    key = f"{profile}:{session_id}"
    if assistant_id:
        payload = {
            "type": "message",
            "id": assistant_id,
            "role": "assistant",
            "content": assistant_text,
            "timestamp": assistant_ts,
        }
        _notify_from_thread(key, payload)
        for delay in (1, 2, 4):
            time.sleep(delay)
            has_clients = bool(ws_connections.get(key) or sse_queues.get(key))
            if has_clients:
                _notify_from_thread(key, payload)
                break
```

### 3. Send the latest message on SSE connect

When a client opens the SSE stream, immediately push the most recent assistant message from the database. This closes the gap if the message arrived before the connection existed:

```python
async def event_generator():
    await register()
    try:
        latest = None
        try:
            with db(profile) as conn:
                row = conn.execute(
                    "SELECT id, role, content, timestamp FROM messages "
                    "WHERE session_id = ? AND role = 'assistant' AND active = 1 "
                    "ORDER BY timestamp DESC LIMIT 1",
                    (session_id,),
                ).fetchone()
                if row:
                    latest = {
                        "type": "message",
                        "id": row["id"],
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                    }
        except Exception:
            latest = None
        if latest:
            try:
                await q.put(f"data: {json.dumps(latest)}\\n\\n")
            except Exception:
                pass
        while True:
            data = await q.get()
            yield data
    finally:
        await unregister()
```

### 4. Keep a polling fallback

Some networks/proxies block both WebSocket and long-lived SSE. Keep a short-polling endpoint that streams new messages by `after_id`:

```
GET /api/sessions/{profile}/{session_id}/poll?after_id={id}
```

Return new assistant rows with `id > after_id`. The UI polls every 500–1000 ms while `active_tasks > 0` or until SSE reconnects.

## Client-side fixes

### Open the live channel as early as possible

For a new session, do not wait for two separate effects. Open SSE immediately after the session is created and before invoking `send_message`. If the backend supports the "latest message on connect" catch-up, the client will receive the answer even if it was generated in the meantime.

### Deduplicate incoming messages

Both retry notify and catch-up-on-connect can deliver the same message twice. Maintain a `Set` of seen message ids in the client and ignore duplicates.

### Clear typing state on any delivery

When a new assistant message is accepted (new id), clear `loading` and any typing indicator.

## How to diagnose

If the UI hangs on "agent is typing":

1. Check `/tmp/bridge.log` for `POST /api/sessions/.../messages` and `GET /api/sessions/.../events`. If the POST is missing, the UI never sent the message (JS crash, CORS, or disabled button).
2. If the POST exists but no `[notify-from-thread]` log line appears for the session, the background task is still running or failed to save the assistant message.
3. If the log shows `[notify-from-thread]` but the UI did not receive it, the client connected **after** the push. Confirm by checking whether the message is already in `state.db`:
   ```bash
   sqlite3 ~/.hermes/profiles/<profile>/state.db \
     "SELECT id, role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 5"
   ```
4. If the message is in the database but the UI has nothing, implement the catch-up-on-connect fix and the retry loop.

## Summary checklist

- [ ] Capture main uvicorn loop on startup.
- [ ] Notify from background thread via `run_coroutine_threadsafe`.
- [ ] Retry notify 1s / 2s / 4s if no clients are connected.
- [ ] Push latest assistant message on SSE connect.
- [ ] Keep `after_id` polling fallback.
- [ ] Client deduplicates messages by id.
