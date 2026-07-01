# Hermes AI Workspace — session state persistence

Keep the user's open chat and history-drawer state across page reloads.

## Why it matters

Without persistence, every F5 drops the user back to the welcome screen. For a workspace tool this feels broken, especially when the user keeps a long history drawer open or works across several agent profiles.

## What to persist

- `profile`: the selected agent/profile name.
- `activeSessionIds`: a map `{ [profileName]: sessionId }` so each profile remembers its own last open chat.
- `tab`: current top-level tab (`chat`, `kanban`, `cron`, `status`).
- `historyOpen`: whether the session-history drawer is open.

Use `localStorage` keys such as:

```
ai-workspace-state          # { profile, tab }
ai-workspace-active-sessions # { [profile]: sessionId }
ai-workspace-history-open    # boolean
```

## Critical architectural pitfall

Do **not** store `activeSessionIds` only inside `ChatView`. If the parent `App` later reads `activeSessionIds` to compute props (for example `initialSessionId={activeSessionIds[selected?.name]}`), the production bundle can throw:

```
activeSessionIds is not defined
```

and render a blank black screen. The crash happens because the variable is out of scope in `App` even though it exists inside the child.

### Correct pattern

Keep the active-session map in `App` and pass it down:

```jsx
// App.jsx
const [activeSessionIds, setActiveSessionIds] = useState(() => {
  try {
    return JSON.parse(localStorage.getItem('ai-workspace-active-sessions')) || {}
  } catch {
    return {}
  }
})

const setActiveSession = (sessionId) => {
  if (!selected) return
  const next = { ...activeSessionIds, [selected.name]: sessionId }
  setActiveSessionIds(next)
  localStorage.setItem('ai-workspace-active-sessions', JSON.stringify(next))
}

// render
{tab === 'chat' && (
  <ChatView
    selected={selected}
    activeSessionIds={activeSessionIds}
    initialHistoryOpen={...}
  />
)}
```

```jsx
// ChatView.jsx
function ChatView({ selected, activeSessionIds, initialHistoryOpen }) {
  const activeSessionId = selected ? activeSessionIds[selected.name] : null
  // ...
}
```

## Restoration flow on mount

1. `App` fetches `/api/profiles`.
2. If `localStorage` has a saved profile, select it; otherwise select the first profile.
3. `ChatView` loads sessions for the selected profile.
4. If `activeSessionIds[profile.name]` exists and the session is still in the list, call `loadSession(savedId)`.
5. Initialize `historyOpen` from `localStorage`.

## References

- `../SKILL.md` — full build instructions.
- `references/ui-compact-layout.md` — history drawer layout.
