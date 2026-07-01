# New chat button and UNIQUE session title constraint

## Symptom

Clicking the "Новый чат" button works once, then stops working. The browser console shows no JS error, but the network request returns HTTP 500. The server log reveals:

```
sqlite3.IntegrityError: UNIQUE constraint failed: sessions.title
```

## Root cause

Hermes `state.db` schema has a `UNIQUE` constraint on `sessions.title` (observed in this workspace). If the UI always sends `title: "NEW_CHAT"` when creating a session, the second click violates the constraint.

## Fix on the Bridge

Generate a unique title server-side whenever the UI sends `NEW_CHAT` (or an empty/missing title):

```python
@app.post("/api/profiles/{name}/sessions")
def create_session(name: str, payload: dict[str, Any] | None = None) -> Session:
    payload = payload or {}
    session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    title = payload.get("title", "AI Workspace chat")
    if title in ("NEW_CHAT", "", None):
        title = f"Новый чат {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')}"
    now = time.time()
    ...
```

## Alternative UI-side fix

If you cannot change the backend, generate a unique title in the UI:

```jsx
const title = input.trim().slice(0, 60) || `Новый чат ${new Date().toLocaleString('ru-RU')}`
fetch(`${API}/profiles/${selected.name}/sessions`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title }),
})
```

## UX notes

- The first message in a new chat can become the session title automatically if Hermes does that; otherwise set it from the first user message.
- Keep the visible button label as "Новый чат"; only the underlying title needs to be unique.
- Do not rely on `title` being user-visible as-is; the UI can shorten or rename it later without touching the database.

## Related pitfall

The same `UNIQUE` constraint can break automated tests or QA loops that create many sessions in a row. Always include a timestamp, counter, or UUID in the title when calling the creation endpoint programmatically.
