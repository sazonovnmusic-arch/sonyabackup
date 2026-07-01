# Real-time chat delivery in Hermes Bridge

## Recommendation: SSE-first, WebSocket as optional, polling as fallback

Browser automation proxies and some VPS network setups block raw WebSocket or close it immediately (`readyState === 4`). Server-Sent Events (SSE) run over plain HTTP, are easier to proxy, and auto-reconnect in most browsers. Therefore:

1. Implement **SSE** as the primary live channel in the UI.
2. Keep a **WebSocket** endpoint on the bridge for environments that support it.
3. Keep an **HTTP poll** endpoint as the final fallback.

## Bridge SSE design

Endpoint:

```
GET /api/sessions/{profile}/{session_id}/events
```

Server behavior:

- Maintain a registry of per-session `asyncio.Queue` instances.
- When a new `assistant` message is written to `state.db`, push a JSON event:
  ```python
  {
      "type": "message",
      "id": assistant_id,
      "role": "assistant",
      "content": assistant_text,
      "timestamp": now,
  }
  ```
- The SSE handler reads from the queue and writes:
  ```
  data: {"type":"message",...}\n\n
  ```

## Thread-safety pitfall

Hermes runs chat in a background thread. If the bridge tries to notify clients from that thread using `asyncio.run()`, it fails because a loop is already running in that thread. The notification must be scheduled on the **main uvicorn event loop**:

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


def notify_clients(session_key: str, payload: dict):
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(_notify_all(session_key, payload), _main_loop)
```

Without this, the assistant response is written to `state.db` but never reaches the open browser tab until the user refreshes.

## Race condition: Hermes finishes before the client connects

When a user sends the first message in a brand-new session, the sequence is often:

1. UI creates the session.
2. UI sends `POST /messages`.
3. Hermes runs and writes the assistant response.
4. Server pushes to zero connected clients because the UI has not opened SSE yet.
5. UI opens SSE a moment later and sees nothing.

Fix it server-side with two mechanisms:

1. **Catch-up on SSE connect**: immediately send the latest assistant message from `state.db` when the client opens the stream.
2. **Retry notify**: after the first push, retry 1s / 2s / 4s if no clients are connected yet. As soon as the UI connects, it receives the message.

See `references/chat-delivery-race-conditions.md` for the full implementation.

## UI subscription pattern

Open the EventSource in a `useEffect` keyed by `activeSessionId`:

```jsx
useEffect(() => {
  if (!activeSessionId || !selected) return
  const url = `${API}/sessions/${selected.name}/${activeSessionId}/events`
  if (esRef.current?.url === url) return   // already connected to this session

  esRef.current?.close()
  const es = new EventSource(url)
  esRef.current = es
  es.onmessage = (e) => {
    const payload = JSON.parse(e.data)
    if (payload.type === 'message') addMessages(payload)
  }
  es.onerror = () => {
    // EventSource auto-reconnects; avoid manual setTimeout loops here.
    // If readyState stays CLOSED for several seconds, fall back to poll.
  }
  return () => es.close()
}, [activeSessionId, selected?.name])
```

Use a ref (`esRef`) instead of state so the connection object is stable across renders. Avoid putting `addMessages` in the dependency array unless it is wrapped in `useCallback` with an empty dependency array; otherwise the effect will re-create the EventSource on every render and can leave `#root` empty if an exception happens before first paint.

## Avoid duplicated user messages in poll fallback

The HTTP poll endpoint should only return messages with `role = 'assistant'` and `id > after_id`. Never include `user` messages from the poll response — the UI already injected the user message optimistically on send.

## Keep typewriter effects out of production chat

Character-by-character rendering causes hundreds of React re-renders and can stall the browser on long responses. Render the full assistant message at once and rely on streaming/push for perceived speed.

## References

- `websocket-chat-pattern.md` — WebSocket-only variant and push registry.
- `chat-polling-patterns.md` — `after_id` polling fallback.
