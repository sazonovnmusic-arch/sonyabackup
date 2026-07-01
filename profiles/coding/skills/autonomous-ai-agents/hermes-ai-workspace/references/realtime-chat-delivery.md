# Hermes AI Workspace — realtime chat delivery

How to push Hermes assistant replies into the React UI instantly, without page refresh.

## Why polling is not enough

Polling every 2 seconds feels laggy and produces "Failed to fetch" flakes when the response arrives late. Use push delivery instead.

## Transport choice

| Transport | When it works | Pitfall |
|-----------|---------------|---------|
| WebSocket | Good for native browsers / local LAN | Browser automation proxies (e.g., Browserbase) often close raw WebSockets immediately (`readyState === 4`). Do not rely on it for automated testing or some remote sessions. |
| Server-Sent Events (SSE) | Works over plain HTTP, survives most proxies | EventSource is one-way (server → client); that's enough for chat. |
| HTTP long-poll | Fallback only | Higher latency, more load. |

**Recommendation for this UI**: implement SSE on both server and client, keep WebSocket server-side support as a future option, but make the UI use SSE only.

## Server-side pattern (FastAPI + Hermes subprocess)

Hermes runs `hermes chat` in a background thread with its own `asyncio.run()`. That thread cannot directly push messages into the uvicorn event loop's queues.

1. Store the main uvicorn loop on startup:

```python
import asyncio
main_loop = asyncio.get_event_loop()
```

2. Keep per-session SSE queues:

```python
sse_queues: dict[str, asyncio.Queue] = {}
```

3. Add the SSE endpoint:

```python
from fastapi import Request
from fastapi.responses import StreamingResponse
import json

async def event_generator(profile: str, session_id: str, request: Request):
    key = f"{profile}:{session_id}"
    queue = asyncio.Queue()
    sse_queues[key] = queue
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield "data: {}\n\n"  # keep-alive ping
    finally:
        sse_queues.pop(key, None)

@app.get("/api/sessions/{profile}/{session_id}/events")
async def session_events(profile: str, session_id: str, request: Request):
    return StreamingResponse(
        event_generator(profile, session_id, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

4. Push from the background Hermes thread using the main loop:

```python
def _notify_all(profile: str, session_id: str, payload: dict):
    key = f"{profile}:{session_id}"
    for q in [ws_connections.get(key), sse_queues.get(key)]:
        if q is None:
            continue
        try:
            if isinstance(q, asyncio.Queue):
                asyncio.run_coroutine_threadsafe(q.put(payload), main_loop)
        except Exception:
            pass
```

**Critical**: if you call `q.put()` directly from the Hermes background thread, it schedules on the thread's temporary loop, not uvicorn's loop, and the event never reaches the client.

5. Push even when Hermes writes the message itself:

Hermes may write the assistant reply directly into `state.db`. In that case the bridge still needs to push a notification, otherwise the UI won't know the reply is ready. Read the latest assistant message from `state.db` right after `hermes chat` finishes and call `_notify_all(profile, session_id, {...})`.

### Race condition on new sessions

For a freshly created session, Hermes can finish and push **before** the UI's `EventSource` connects. The client then opens SSE after the push and never receives the reply.

Fix both server and client:

- **Server**: when a client subscribes to `/events`, immediately send the latest existing assistant message for that session as the first event. This catches up clients that connect after the reply is already in `state.db`.
- **Server**: retry the push from the background thread a few times (e.g., 1 s, 2 s, 4 s) until at least one SSE or WebSocket client is connected; stop retrying once someone receives it.

```python
# inside _run_hermes_task after saving the assistant message
payload = {
    "type": "message",
    "id": assistant_id,
    "role": "assistant",
    "content": assistant_text,
    "timestamp": assistant_ts,
}
_notify_all(profile, session_id, payload)
for delay in (1, 2, 4):
    time.sleep(delay)
    if ws_connections.get(key) or sse_queues.get(key):
        _notify_all(profile, session_id, payload)
        break
```

These two fixes eliminate the "typing indicator hangs and nothing appears" symptom that looks like a broken chat but is actually a timing gap.

## Client-side pattern (React)

Keep a stable `useEffect` that opens/closes the EventSource whenever the active session changes. Do not recreate it on every render.

```jsx
const esRef = useRef(null)

useEffect(() => {
  if (!activeSessionId || !selected) {
    if (esRef.current) { esRef.current.close(); esRef.current = null }
    return
  }
  const key = `${selected.name}:${activeSessionId}`
  if (esRef.current?.__key === key) return

  const es = new EventSource(`${EVENTS_URL}/${selected.name}/${activeSessionId}/events`)
  es.__key = key
  esRef.current = es

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'message') addMessages(data)
    } catch (err) {
      console.error('[SSE] parse', err)
    }
  }
  es.onerror = () => {
    es.close()
    setTimeout(() => {
      if (esRef.current?.__key === key) openEventSource(selected.name, activeSessionId)
    }, 2000)
  }

  return () => { es.close(); esRef.current = null }
}, [activeSessionId, selected, addMessages])
```

Pitfalls:
- Do not switch to WebSocket inside `onerror` — if the browser blocks WebSockets, you'll loop between transports.
- `addMessages` must be wrapped in `useCallback` or the effect will reconnect on every message.
- Closing the old EventSource before opening a new one prevents duplicate connections.

## Verifying it works

1. Open browser devtools → Network → EventStream.
2. Send a message. You should see the SSE connection open and, after the agent replies, a `data:` line arrive.
3. If no line arrives but the message is in `state.db`, the push did not leave the background thread — check `run_coroutine_threadsafe` and `main_loop`.
4. If the line arrives but the UI doesn't render it, the `onmessage` handler or state update is broken.

## References

- `../SKILL.md` — full AI Workspace build instructions.
- `references/ai-workspace-ui-rules.md` — visual style and chat UX rules.
