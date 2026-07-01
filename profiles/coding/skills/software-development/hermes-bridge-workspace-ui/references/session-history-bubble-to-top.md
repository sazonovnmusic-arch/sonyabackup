# Session history bubble-to-top animation

When the user sends a message inside an older session, the session should immediately jump to the top of the history list with a smooth animation — just like ChatGPT or DeepSeek do.

## Why the naive server-only approach feels broken

If you only update `updated_at` / `ended_at` on the server and refresh the list later, the user sees the old order for several seconds (or until the next full reload). This feels laggy and "криво".

The fix is a **local optimistic update** in React plus a **CSS transition**.

## Backend change

Sort the history by the last activity timestamp, not by creation time:

```python
@app.get("/api/profiles/{name}/sessions")
def list_sessions(name: str) -> list[Session]:
    with db(name) as conn:
        rows = conn.execute("""
            SELECT id, title, source, started_at, ended_at, message_count
            FROM sessions
            WHERE archived = 0
            ORDER BY COALESCE(ended_at, started_at) DESC
            LIMIT 100
        """).fetchall()
        ...
```

Also touch `ended_at` when a message is sent, so the server-side list is already correct:

```python
@app.post("/api/sessions/{profile}/{session_id}/messages")
def send_message(profile: str, session_id: str, req: ChatRequest):
    ...
    try:
        with db(profile) as conn:
            conn.execute("UPDATE sessions SET ended_at = ? WHERE id = ?",
                         (time.time(), session_id))
            conn.commit()
    except Exception:
        pass
    thread = threading.Thread(target=_run_hermes_task, args=(...))
    thread.start()
    return {"status": "processing", "task_id": task_id, "session_id": session_id}
```

## Frontend optimistic update

In the `send` handler, move the active session to index 0 immediately — before the network request returns:

```jsx
const send = async (e) => {
  e.preventDefault()
  if (!selected || loading) return
  if (!input.trim() && attachedFiles.length === 0) return

  let sessionId = activeSessionId
  if (!sessionId) {
    // create new session...
  }

  setMessages(prev => [...prev, userMsg])
  setInput('')
  setLoading(true)
  setError(null)

  // Optimistic bubble-to-top
  if (sessionId) {
    setSessions(prev => {
      const existing = prev.find(s => s.id === sessionId)
      if (!existing) return prev
      const now = Date.now() / 1000
      const updated = { ...existing, updated_at: now }
      return [updated, ...prev.filter(s => s.id !== sessionId)]
    })
  }

  // continue with fetch(...)
}
```

## CSS animation for the top item

Add a keyframe in `index.css`:

```css
@keyframes slide-top {
  0% { transform: translateY(-12px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}
.animate-slide-top {
  animation: slide-top 0.35s ease-out;
}
```

Apply it only to the first item in the mapped list:

```jsx
{sessions.map((s, index) => {
  const isActive = activeSessionId === s.id
  return (
    <div
      key={s.id}
      className={cls(
        'group w-full text-left px-3 py-2.5 transition-all duration-300 ease-out ...',
        isActive ? 'bg-[var(--surface-2)] text-[var(--accent)]' : 'text-[var(--text)] hover:bg-[var(--surface-2)]',
        index === 0 && 'animate-slide-top'
      )}
    >
      ...
    </div>
  )
})}
```

## Pitfalls

- Do not animate **every** list item — only the top one, otherwise the whole list jiggles.
- Keep `key={s.id}` stable; React will reuse the DOM node and the animation will run on the newly-top session.
- The server-side `ORDER BY` must match the local order (`COALESCE(ended_at, started_at) DESC`), otherwise the list will jump again on the next full reload.
- For a brand-new session created from the input, it is already inserted at index 0, so no extra bubble animation is needed.
