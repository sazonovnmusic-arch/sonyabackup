# Compact AI Workspace UI layout

When the full three-column layout (agents sidebar + session history + chat) consumes too much horizontal space, collapse the outer navigation and history into compact controls.

## Recommended layout

```
+----+--------------------------------------------------+
| AI |  coding  ☰  + Новый чат   [Чат][Kanban][Cron]   |
|    |                                                  |
| CO |  Chat messages...                                |
|    |                                                  |
| IN |  [📎] [Message...                    ] [Send]  |
|    |                                                  |
| YO |                                                  |
|    |                                                  |
| DE |                                                  |
+----+--------------------------------------------------+
```

- Left sidebar: **64px wide**, only circular agent initials with a status dot.
- History: **overlay drawer** (260px), toggled via ☰ in the chat header.
- Tabs (Чат/Kanban/Cron/Статус): placed in the **chat header**, not a separate bottom nav.

## Implementation notes (React + Tailwind)

1. Agent sidebar:
   ```jsx
   <aside className="w-16 flex-shrink-0 ...">
     {agents.map(agent => <AgentIcon key={agent.name} agent={agent} />)}
   </aside>
   ```
   Show full name in a tooltip on hover.

2. Header toggle for the drawer:
   - Same button toggles open/close.
   - Show `☰` when the drawer is closed, `✕` when it is open.
   - Keep it on the **left side** of the header next to the agent name.
   - Also add a `✕` close button inside the drawer header for discoverability.

3. History drawer (overlay, not inline):
   ```jsx
   {historyOpen && (
     <>
       <div className="absolute inset-0 z-20 bg-black/40" onClick={() => setHistoryOpen(false)} />
       <aside className="absolute left-0 top-0 h-full w-64 z-30 ...">
         ...session list...
       </aside>
     </>
   )}
   ```
   Do **not** use `w-0` inline drawers; they still reserve DOM/flex space and create visual artifacts. Use `absolute left-0 top-0 h-full` (not `bottom-0`) so the drawer stretches the full viewport height inside the flex container.

4. Chat header contains:
   - ☰ / ✕ toggle for history (left side, next to agent name)
   - Agent avatar + name + model/provider
   - "+ Новый чат" button
   - Tab buttons

## Why this works

- Chat gets nearly the full viewport width.
- Agent switching is one click.
- History is available on demand without permanently sacrificing space.
- Tabs stay visible regardless of scroll position.

## Session-state persistence across reloads

A workspace UI must not lose context on F5. Persist and restore:

- selected agent profile
- active session id per profile
- selected tab
- history drawer open/closed state

Use `localStorage` keys such as:

- `ai-workspace-state` → `{ profile, tab }`
- `ai-workspace-active-sessions` → `{ profileName: sessionId, ... }`
- `ai-workspace-history-open` → `true | false`

On app mount, read these keys before defaulting to the first profile/welcome screen.

## When to keep the old layout

Keep the wide sidebar if:
- The user explicitly wants to see all sessions at all times.
- Screen width is very large (>1600px) and the extra columns don't hurt.
- The workspace has very few agents and many long session titles.
