# Recipe: render heavy chat sessions in the Hermes Workspace UI

A Hermes session can accumulate hundreds of messages, each several kilobytes long (especially compaction summaries and tool results). Sending the full JSON to the browser and rendering it all at once freezes React and makes the chat unusable (header/input disappear, scroll locks, only the spinner is shown).

Use the patterns below in the Workspace UI chat view.

## Server-side pagination

Add `limit` / `offset` query parameters to the session-messages endpoint so the UI requests only the tail of the conversation.

FastAPI example:

```python
@app.get("/api/sessions/{profile}/{session_id}/count")
def get_session_message_count(profile: str, session_id: str) -> dict[str, int]:
    with db(profile) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages WHERE session_id = ? AND active = 1",
            (session_id,),
        ).fetchone()
        return {"count": row["cnt"] if row else 0}


@app.get("/api/sessions/{profile}/{session_id}")
def get_session(
    profile: str,
    session_id: str,
    limit: int | None = None,
    offset: int = 0,
    order: str = "asc",
) -> list[Message]:
    with db(profile) as conn:
        sql = """
            SELECT id, role, content, timestamp, active
            FROM messages
            WHERE session_id = ? AND active = 1
            ORDER BY timestamp {order}
        """.format(order="ASC" if order.lower() != "desc" else "DESC")
        params: list[Any] = [session_id]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [limit, offset]
        rows = conn.execute(sql, params).fetchall()
        ...
```

## UI load sequence

1. Fetch the total count.
2. Compute `offset = max(0, count - PAGE_SIZE)`.
3. Request `limit = PAGE_SIZE` messages starting at that offset.
4. Render only the returned page.

```js
const PAGE_SIZE = 20

const loadSession = async (sessionId) => {
  const { count } = await fetch(`/api/sessions/${profile}/${sessionId}/count`).then(r => r.json())
  const offset = Math.max(0, count - PAGE_SIZE)
  const messages = await fetch(
    `/api/sessions/${profile}/${sessionId}?limit=${PAGE_SIZE}&offset=${offset}&order=asc`
  ).then(r => r.json())
  setMessages(messages)
  setPage(offset)
}
```

## "Load more" button

Place a button above the messages. On click, fetch the next older page and prepend it to the list.

```js
const loadMore = async () => {
  const newPageStart = Math.max(0, page - PAGE_SIZE)
  const offset = Math.max(0, newPageStart - PAGE_SIZE)
  const limit = page - offset
  if (limit <= 0) return
  const older = await fetch(
    `/api/sessions/${profile}/${sessionId}?limit=${limit}&offset=${offset}&order=asc`
  ).then(r => r.json())
  setMessages(prev => [...older, ...prev])
  setPage(offset === 0 ? totalCount : offset)
}
```

Show the button only when `page > 0`.

## Collapse oversized messages

Even 20 messages can be too much if each is a 10 KB compaction summary. Render each message through a component that caps the visible length and offers an expand link.

```jsx
function MessageText({ content, max = 3000 }) {
  const [expanded, setExpanded] = useState(false)
  const shouldCollapse = content.length > max
  const text = expanded || !shouldCollapse ? content : content.slice(0, max) + '…'
  return (
    <>
      {text}
      {shouldCollapse && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="block mt-2 text-xs text-[var(--text-dim)] hover:text-[var(--accent)] transition"
        >
          {expanded ? 'Свернуть' : 'Показать полностью'}
        </button>
      )}
    </>
  )
}
```

Use `whitespace-pre-wrap break-words` on message bubbles to keep long code blocks readable without breaking the layout.

## Avoid auto-loading the first session

Do not automatically open the most recent session when the user switches agents. Large sessions can block the initial render. Let the user pick a session from the history drawer, or start a new chat.

```js
useEffect(() => {
  if (!selected) return
  setMessages([])
  setPage(0)
  fetch(`/api/profiles/${selected.name}/sessions`)
    .then(r => r.json())
    .then(setSessions)
    .catch(setError)
  // intentionally do NOT auto-load data[0]
}, [selected])
```

Only restore the previously active session (`activeSessionIds[selected.name]`) if the user explicitly expects it.

## Layout must stay fixed-height

A common symptom of chat "disappearing" is the outer flex container stretching. Pin all chat containers:

- Outer layout: `h-screen flex flex-col overflow-hidden`.
- Chat wrapper: `flex-1 min-h-0 flex flex-col`.
- Messages area: `flex-1 min-h-0 overflow-y-auto`.
- Header and composer: `flex-shrink-0`.

Never use an unbounded `min-height: auto` inside a flex-1 column, or a huge message list will push the header and composer off-screen.

## Optimizing the Status tab

The Status endpoint must not scan every message body. Use a single indexed query to get the latest message only.

FastAPI helper:

```python
_status_cache: dict[str, tuple[float, tuple[str, float | None]]] = {}

def _agent_activity(name: str) -> tuple[str, float | None]:
    """Returns (status, last_active_at). Cached for 10 seconds."""
    now = time.time()
    if name in _status_cache:
        cached_at, value = _status_cache[name]
        if now - cached_at < 10:
            return value
    try:
        with db(name) as conn:
            row = conn.execute(
                """
                SELECT timestamp AS last_ts, role AS last_role
                FROM messages
                WHERE session_id IN (
                    SELECT id FROM sessions WHERE source = 'api' AND archived = 0
                ) AND active = 1
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ).fetchone()
            if not row:
                value = ("idle", None)
                _status_cache[name] = (now, value)
                return value
            last_active = float(row["last_ts"])
            last_role = row["last_role"]
            if last_role == "user" and (now - last_active) < 300:
                value = ("waiting", last_active)
            elif (now - last_active) < 300:
                value = ("working", last_active)
            else:
                value = ("idle", last_active)
            _status_cache[name] = (now, value)
            return value
    except Exception:
        return "unknown", None
```

Also add a covering index on first connection:

```sql
CREATE INDEX IF NOT EXISTS idx_messages_session_active_timestamp
ON messages(session_id, active, timestamp)
```

Do **not** use `SUM(CASE WHEN role = ...)` over the full `messages` table — it reads every row including large compaction summaries and makes the Status tab lag.

## Welcome screen layout

When no session is selected, the chat area should not show an empty message list and a bottom composer. Render a centered welcome screen instead:

- Circular profile avatar (initials, later swapped for a PNG icon).
- Heading: `На связи {profile}, чем могу помочь?` (or locale equivalent).
- Short hint: "Напишите сообщение ниже."
- A rounded, pill-like input with attach button and submit button centered in the viewport.

```jsx
function WelcomeInput({ profile, onSend }) {
  const [input, setInput] = useState('')
  return (
    <div className="h-full flex flex-col items-center justify-center px-4">
      <div className="w-16 h-16 rounded-full border border-[var(--accent)] bg-[var(--surface-2)] text-[var(--accent)] flex items-center justify-center text-lg font-medium mb-6">
        {profile.name.slice(0, 2).toUpperCase()}
      </div>
      <h2 className="text-xl text-[var(--text)] mb-2">
        На связи {profile.name}, чем могу помочь?
      </h2>
      <p className="text-sm text-[var(--text-dim)] mb-8">
        Напишите сообщение ниже.
      </p>
      <form onSubmit={...} className="w-full max-w-2xl">
        <div className="subtle-input flex items-center gap-2 pr-2 rounded-3xl">
          <button type="button" className="subtle-btn w-10 h-10 rounded-full">+</button>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={`Сообщение ${profile.name}…`}
            className="flex-1 bg-transparent px-2 py-3 outline-none"
            autoFocus
          />
          <button type="submit" className="subtle-btn-primary px-5 py-2 rounded-2xl">
            Отправить
          </button>
        </div>
      </form>
    </div>
  )
}
```

On submit, create a new session and send the first message. Hermes will write both messages into `state.db`.

## Design preference for this workspace

When the user asks for a "минималистичный дизайн" (minimalist design) for this control center, use:

- Near-black background (`#0a0a0a`) with subtle dark surfaces (`#111111`, `#161616`).
- Sky-blue accent (`#0ea5e9`) instead of green or purple.
- Rounded corners (`rounded-lg`/`rounded-xl`/`rounded-2xl`/`rounded-3xl`) on buttons, cards, inputs, message bubbles, and avatars.
- System sans-serif font (Inter/SF Pro), not pixel or arcade fonts.
- Thin 1px borders, no harsh 2px arcade borders or box-shadow presses.

Avoid pixel/retro styles unless the user explicitly asks for an arcade aesthetic. If they try it and say "too arcade" or "слишком аркадный", revert to the rounded minimal dark style above immediately.

## File-edit hygiene

Hermes' `read_file` tool can prefix lines with line numbers (`1|content`). If that content is written back to a JSX/JS/TS file unchanged, the file becomes invalid and the UI renders a blank white screen. Always strip line-number prefixes before writing code files, or use `write_file` with freshly generated content rather than echoing raw `read_file` output.

## Verification

- [ ] Opening a session with 400+ messages shows the last page within a second.
- [ ] Header, tabs, and input remain visible.
- [ ] "Load more" button prepends older messages.
- [ ] Long messages render a "Show more" link.
- [ ] Switching agents does not freeze the UI.
- [ ] Status tab loads in under a second for all profiles.
- [ ] Blank white screen after a code edit is resolved by checking for line-number prefixes in the edited file.
