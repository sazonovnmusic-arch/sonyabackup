---
name: hermes-ai-workspace
description: "Build web-based AI Workspace / Control Center dashboards on top of Hermes Agent."
version: 1.1.0
author: Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, ai-workspace, dashboard, bridge, multi-agent, react, fastapi]
    homepage: ""
    related_skills: [hermes-agent]
    linked_files:
      references:
        - references/minimal-dark-ui.css
        - references/pixel-terminal-ui.md
        - references/ai-workspace-ui-rules.md
        - references/cron-jobs-json-parser.md
        - references/cron-integration.md
        - references/hermes-session-resume.md
        - references/file-attachments.md
        - references/ui-compact-layout.md
        - references/realtime-chat-delivery.md
        - references/chat-message-rendering.md
---

# Hermes AI Workspace

Build a web-based "AI Office" where each Hermes profile appears as an agent/employee with chat, task board, and status dashboard.

## When to use

- User wants a web UI over Hermes instead of only Telegram/CLI.
- Need agent directory, per-agent chat history, Kanban tasks, and agent status.
- Building a control-center / operating-system metaphor on top of Hermes.

## Architecture

```
React UI (Vite/Next.js)  ←→  FastAPI Bridge  ←→  Hermes Core  ←→  LLMs / tools
```

- **Bridge** reads `~/.hermes/profiles/` and each profile's `state.db`.
- **Bridge** creates empty SQLite sessions so `hermes chat --resume` works, then runs `hermes --profile <name> chat -q <msg> --resume <session_id>`.
- **Bridge** stores tasks/calendar in a separate `workspace.db`.
- **UI** proxies `/api` to the bridge.

## Project layout

```
ai-workspace/
├── bridge/
│   ├── main.py          # FastAPI app
│   ├── requirements.txt
│   └── workspace.db     # tasks, statuses
└── ui/
    ├── src/App.jsx
    ├── src/main.jsx
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── postcss.config.cjs
```

## Key API routes

- `GET  /api/profiles`
- `GET  /api/profiles/{name}/sessions`
- `POST /api/profiles/{name}/sessions`
- `GET  /api/sessions/{profile}/{session_id}`
- `POST /api/sessions/{profile}/{session_id}/messages`
- `GET  /api/agents/status`
- `GET  /api/tasks`, `POST`, `PATCH`

## Critical pitfall: Hermes session creation

`hermes chat --resume <id>` will ignore or fail on a session row that lacks the fields Hermes expects. When creating a session via direct SQLite insert, populate at least:

- `model`
- `system_prompt`
- `billing_provider`
- `billing_base_url`
- `estimated_cost_usd = 0.0`
- `cost_status = 'unknown'`
- `cost_source = 'none'`

See `references/hermes-session-resume.md` for the exact schema insert.

Keep the session **empty** (no messages). Then `hermes chat -q <msg> --resume <id>` will write the user message and assistant reply itself, avoiding duplicates.

## UI session-state pattern

When multiple agents each have multiple chats:

1. Store active session per agent, e.g. `activeSessionIds[agentName]`.
2. On agent switch, load that agent's session list; if saved active session exists, restore it; otherwise open the most recent.
3. New sessions append to the list; old sessions remain clickable.

This gives ChatGPT-like behavior: context persists across agent switching.

## Session list UX

Render each session with:
- truncated title (use a readable, non-tiny font — aim for 15–16 px)
- creation date (short)
- message count
- active indicator for currently open session

Make the list items tall enough to scan comfortably. Compact is good, but 10 px rows are too small for a dense history list. Use generous vertical padding (`py-2.5` to `py-3.5`) and clear hover/active backgrounds rather than borders. The user explicitly asked for larger session blocks when the initial compact version felt too small.

## Production `serve` + API base fix

When the React UI is built with Vite and served by `npx serve -s dist -l 3000`, the dev proxy is gone. If `API` is set to a relative `/api`, requests will hit `http://ui-host:3000/api` and fail silently, producing an empty agent list or broken chat.

Fix: hardcode the bridge origin in the production build:

```jsx
const API = 'http://<bridge-host>:8123/api'
```

Alternatively, run `serve` behind an nginx reverse proxy that forwards `/api` to the bridge. For a standalone setup, the absolute URL is simpler and more reliable.

Pitfall: the UI may appear to load but show no agents and no errors in the UI because `fetch('/api/profiles')` returns the `index.html` fallback or a 404. Always verify the network tab shows requests going to `:8123/api`.

## UI crash guard: validate every message object

Hermes `state.db` can contain messages with unexpected shapes (e.g. tool rows, null content, or missing timestamps). The UI must defensively validate before using fields:

```jsx
const visible = data.filter(m => m && (m.role === 'user' || m.role === 'assistant') && m.timestamp != null)
```

When polling for an assistant reply, guard the poll response:

```jsx
if (!data.message || data.message.timestamp == null) return
const msg = {
  ...data.message,
  content: data.message.content || '',
  timestamp: data.message.timestamp || Date.now() / 1000,
}
```

Without this guard, a malformed message can throw `Cannot read properties of undefined (reading 'timestamp')`, break React rendering, and make the user see "Failed to fetch" even though the bridge succeeded.

## Rendering long / high-volume chat sessions

Hermes sessions can grow to hundreds of messages with very large compaction/system-prompt contents. Naively loading and rendering the entire `state.db` message list in React will freeze or blank the chat area.

Fix at the Bridge, not just the UI:

1. Add server-side pagination on `GET /api/sessions/{profile}/{id}` with `?limit=` and `?offset=`.
2. Add `GET /api/sessions/{profile}/{id}/count` so the UI knows how many messages exist.
3. Load only the **last 20 messages** when opening a session; render a "Load N more" button at the top of the list.
4. Collapse individual messages longer than ~3000 chars behind an expand link.
5. Always preserve `min-w-0 break-words` on message bubbles so long unbroken strings do not blow out the layout.
6. Add a database index `(session_id, active, timestamp)` on the Hermes `messages` table if the Bridge queries it often; use `CREATE INDEX IF NOT EXISTS` so it is safe to run on existing state.db files.
7. Cache lightweight status queries (e.g., `last_active_at`) for ~10 seconds in memory; they do not need fresh data on every tab switch.

Pitfall: if the UI attempts to auto-scroll to the bottom on every message load, large sessions can "trap" the user at the bottom and make header/input disappear. Scroll-to-bottom should only run after user-initiated sends, not on initial session load.

### Status-tab performance

The simplest implementation scans every message row for every profile. With large sessions this lags visibly. Optimize:

- Do **not** read `content` or compute `SUM/CASE` over the full table just for a status dot.
- Use one query per profile: `SELECT timestamp, role FROM messages WHERE session_id IN (...) AND active=1 ORDER BY timestamp DESC LIMIT 1`.
- Ensure an index on `(session_id, active, timestamp)` exists.
- Cache the result for 5–10 seconds.
- In the UI, call `/api/agents/status` (not `/api/agents`) and show a loading state.

## File attachments in chat

Bridge endpoints (see `references/file-attachments.md` for full recipe and pitfall notes):

- `POST /api/sessions/{profile}/{session_id}/files` — multipart upload, saved to `bridge/files/<profile>/<session_id>/`.
- `GET /api/sessions/{profile}/{session_id}/files` — list attached files.
- `GET /api/files/{profile}/{session}/{filename}` — download file.

Important pitfall: whenever file handling code is added to an existing bridge, verify that `import shutil` and `import mimetypes` are at the top of `main.py`; missing imports are a common source of runtime `NameError`s after iterative patches. Also verify `UploadFile` is imported from `fastapi` if file endpoints are added.

On message send, pass `attached_files: ["name.txt", "..."]` in `ChatRequest`. The bridge:

- inserts text file contents into the prompt wrapped in `--- File: name ---` markers;
- appends `--image /path/to/img.png` to the `hermes chat` command for image attachments.

Hermes CLI does **not** support a generic `--file` flag, only `--image`. Inline textual attachments as prompt text.

UI pattern: hidden file input + paperclip button + drag-and-drop overlay + per-session file chips with toggle selection.

## Cron integration

Hermes has a built-in `hermes cron` subsystem. In the AI Workspace UI, add a dedicated **Cron** tab (do not put cron jobs directly on the Kanban board):

- `GET /api/cron` — list jobs across all profiles.
- `POST /api/cron` — create job via `hermes cron create --name ... --schedule ... --prompt ...`.
- `POST /api/cron/{id}/run|pause|resume` — run or toggle job.
- `DELETE /api/cron/{id}` — remove job.
- `POST /api/cron/{id}/tasks` — create a Kanban task from this cron job.

### Critical: where Hermes actually stores cron jobs

`hermes cron list` only returns jobs for the **currently active profile**. The Hermes scheduler keeps per-profile cron state in JSON files:

```
~/.hermes/profiles/<profile>/cron/jobs.json
```

Each file has shape `{"jobs": [{"id", "name", "prompt", "schedule": {"expr"/"display"}, "enabled", "state", "last_run_at", "next_run_at", ...}]}`.

The Bridge's `/api/cron` endpoint must read these `jobs.json` files directly for every discovered profile and merge them, optionally filtering by `?profile=`. Only fall back to `hermes cron list` if you specifically need runtime scheduler state that isn't in the JSON.

See `references/cron-jobs-json-parser.md` for the exact parser and `references/cron-integration.md` for the control-endpoint recipe.

Cron jobs can **spawn** Kanban cards, but they themselves are automation triggers, not board cards.

## Compact UI layout

When the sidebar + history + chat layout consumes too much horizontal space, switch to:

- **64px agent icon sidebar** (initials + status dot, tooltip on hover). Avatars stay square-ish with soft rounding, not circles.
- **History as a slide-in drawer** that pushes the chat area (flex width transition), not an overlay that covers the chat.
- **Tabs in the chat header** instead of a separate bottom nav.
- The history drawer remains open until the user explicitly closes it (clicking a session should not auto-close it).

Pitfall: an absolute overlay drawer makes the chat unreadable on small screens. Use a real flex column with `transition-all duration-200` on width; when closed, set width to `0` and hide children, but do not let an unclosed absolute layer remain on top.

See `references/ui-compact-layout.md` for the React/Tailwind recipe.

## Agent status tab (3-dot menu)

Each agent card can expose a small dropdown with actions such as **Restart / Stop / Start / Delete**.

Pitfalls:
- Use the field that the API actually returns for identity. If `/api/agents/status` returns `profile`, use `a.profile` everywhere. Using a missing field like `a.name` produces `undefined === undefined` which makes every menu appear "open" by default.
- Keep the menu compact: small text (10–11px), minimal padding, auto width.
- The menu must start closed; only open on click of the ⋮ button.
- Any destructive action (Delete profile) must show a centered confirmation modal. **Never invoke destructive profile endpoints as a test or without explicit user permission** — it can wipe a live Hermes profile.

## Destructive operations guard

Commands or endpoints that delete, stop, restart, clear, or mutate a Hermes profile are dangerous to the user's setup. Rules:

1. **Never verify/test destructive endpoints against a real user profile.** Use a throwaway test profile or test the logic in isolation.
2. **Always back up before destructive ops** if the user asks for them.
3. **Always ask/confirm the exact target** before running delete/clear/restart on a live profile.
4. Prefer disabling UI controls over silently executing destructive backend calls.

## Pixel / terminal / retro UI style

If the user explicitly asks for a pixel/arcade/terminal look, load `references/pixel-terminal-ui.md` and apply it globally. Be careful: that style quickly feels too "arcade" for users who asked for "minimalist".

If the user says something like "слишком аркадный", "убери пиксельный", or "верни минималистичный", revert to the clean dark system documented above rather than softening the pixel style.

### Default clean minimalist dark style

```css
:root {
  --bg: #0a0a0a;
  --surface: #111111;
  --surface-2: #171717;
  --surface-3: #1f1f1f;
  --border: #252525;
  --border-2: #303030;
  --text: #f0f0f0;
  --text-dim: #808080;
  --accent: #0ea5e9;
  --accent-hover: #0284c7;
  --accent-2: #a855f7;
  --danger: #ef4444;
}

body {
  background: var(--bg);
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "SF Pro", sans-serif;
  font-size: 14px;
}
```

Rules:
- 1px borders, no hard drop shadows.
- Strong rounding: buttons/inputs use `rounded-lg`/`rounded-xl`/`rounded-2xl`; profile avatars stay **square-ish with soft rounding** (`rounded-md`/`rounded-xl`), not circular.
- System sans-serif, normal weights.
- Blue/cyan accent (#0ea5e9) for primary actions, not green.
- Keep the welcome-screen centered input.
- Session-list items are plain text without borders; active item gets a subtle background, hover gets a hover background.

See `references/pixel-terminal-ui.md` for the full pixel variant if explicitly requested.

## Empty-chat welcome screen

For a ChatGPT/DeepSeek-style first impression, when no session is selected show a centered welcome screen with:

- agent name/avatar (initials or icon for the selected profile, not a generic "AI" badge),
- a short hint (do not use "Open history or type below" — keep it minimal, e.g. "Напишите сообщение ниже."),
- a large, centered message input with a prominent send button,
- the regular bottom input bar only appears once a session is active.

The welcome heading should read **"На связи {profile}, чем могу помочь?"** (or localized equivalent). Avoid placeholder text like "Open history or type below to start".

The welcome input should use the same design tokens as the rest of the app. If a specific visual style is requested, apply it globally; if the user rejects the current style (e.g., pixel/arcade), fall back to the clean dark system documented below.

## Chat behavior

- Render assistant messages with Markdown formatting, clean typography, and a ChatGPT-style layout: user in a bubble, assistant on a plain background. See `references/chat-message-rendering.md`.
- Use typewriter animation only if the user asks for it; split by whitespace chunks (~22 ms), not characters, to avoid lag.
- Push new assistant messages via SSE with thread-safe event-loop scheduling. See `references/realtime-chat-delivery.md`.
- Poll only as fallback.
- Load full conversation history when opening a session; paginate very large sessions.

### Session state persistence

Preserve the user's working context across page reloads:

- Save active profile, active session per profile, selected tab, and history-drawer open/closed state to `localStorage` (or URL hash as fallback).
- On mount, restore the saved profile, its last active session, and the drawer state.
- Without this, every reload drops the user back to a welcome screen, which feels broken for a workspace tool.

### Architecture pitfall: where active-session state lives

If the active-session map (`activeSessionIds[profileName]`) is stored inside a child component such as `ChatView`, but the parent `App` reads it to pass props (e.g. `initialSessionId`), the production build can throw `activeSessionIds is not defined` and render a blank black screen. Keep the active-session state at the `App` level and pass `activeSessionIds` / setter down through props. The child `ChatView` derives its current session from props, not local state.

See `references/session-state-persistence.md` for the exact pattern and the blank-screen fix.

### "New chat" semantics

Match ChatGPT behavior:

- The **New chat** button only clears the current selection and shows the welcome-screen composer. It must **not** create a server-side session immediately.
- Create the actual session only when the user sends the first message; use the first ~60 characters of the message (or a timestamped fallback) as the title to avoid `UNIQUE` collisions on `sessions.title`.

### History ordering and live updates

Sort sessions by most recent activity (`COALESCE(ended_at, started_at) DESC`). When the user sends a message, immediately bubble that session to the top of the list locally and update `ended_at` on the bridge, so the list reflects reality without waiting for a refresh.

## Hermes home path pitfall

When the Bridge process inherits `HERMES_HOME` from an active Hermes session, it may point at a single profile directory (`~/.hermes/profiles/coding`) instead of `~/.hermes`. Always resolve the Hermes home explicitly:

```python
HERMES_HOME = Path(os.environ.get("BRIDGE_HERMES_HOME", Path.home() / ".hermes"))
```

Ignore the inherited `HERMES_HOME` unless the user intentionally sets `BRIDGE_HERMES_HOME`.

## Next steps / extensions
## Project archive & restore

When pausing a large UI project, archive the code + state + instructions and clean heavy dev artifacts:

```bash
mkdir -p ~/ai-workspace-archive
tar --exclude='ai-workspace/ui/node_modules' \
    --exclude='ai-workspace/bridge/.venv' \
    --exclude='ai-workspace/ui/dist' \
    -czf ~/ai-workspace-archive/ai-workspace-$(date +%Y%m%d-%H%M%S).tar.gz ai-workspace
```

Include in the archive:
- `README-STATE.md` — what works, what's unfinished, key files, how to run.
- `restore.sh` — one-command redeploy (reinstall venv/deps, build UI, start services).

Only delete dev caches and heavy transient files (`node_modules`, `.git`, Playwright cache, npm cache). Never delete Hermes profiles, their `state.db`/cron configs, or archives the user asked to keep.

Stop running services first so the archive does not capture locked databases or partial state:

```bash
pkill -f "serve -s dist -l 3000"
pkill -f "uvicorn main:app --host 0.0.0.0 --port 8123"
```

## AionUi headless alternative

If building a polished custom UI becomes too time-consuming, AionUi is a ready-made multi-agent desktop/WebUI that officially supports Hermes via ACP. It can run headless on the same VPS.

### How AionUi connects to Hermes

AionUi speaks **ACP (Agent Control Protocol)** — JSON-RPC over stdin/stdout. Hermes already supports it:

```bash
hermes acp
```

In local desktop mode AionUi expects the `hermes` binary in PATH. On a headless server, run the WebUI build instead.

### Install AionUi WebUI on a headless VPS

1. Check resources (`free -h && df -h /`). The `.deb` is ~400 MB and needs ~1 GB free.
2. Install Xvfb (virtual display — Electron requires a display server):
   ```bash
   apt-get install -y xvfb
   ```
3. Download the latest `.deb` from releases:
   ```bash
   curl -L -o AionUi.deb https://github.com/iOfficeAI/AionUi/releases/latest/download/AionUi-linux-amd64.deb
   dpkg -i AionUi.deb
   apt-get install -f -y
   ```
4. Start headless WebUI:
   ```bash
   cd /opt/AionUi
   xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
     /opt/AionUi/AionUi --webui --remote --no-sandbox
   ```
5. Access at `http://SERVER_IP:25808`.
6. Reset admin password via API:
   ```bash
   curl -s -X POST http://localhost:25808/api/webui/reset-password
   curl -s http://localhost:25808/api/auth/internal/users/system
   ```

### Trade-offs vs. custom AI Workspace

| Custom AI Workspace | AionUi |
| --- | --- |
| Full control over design/behavior | Polished out-of-the-box UI |
| Lightweight (React + FastAPI) | Heavy (Electron + Rust backend) |
| Integrates our Kanban/Cron/tasks natively | Built-in multi-agent, cron, status, file preview |
| Must debug SSE, state, animations | ACP-based chat, tested with Hermes |
| Sky-blue ChatGPT-style dark theme | AionUi's own Arco Design theme |

Best path: try AionUi headless for a quick demo, then decide whether to migrate or return to the custom UI archive.

See `references/aionui-headless-vps.md` for the exact commands and credentials API.

## Next steps / extensions
- Add auth / login before exposing to the internet.
- Use nginx + SSL for external access.
- Use WebSockets/SSE for live status updates (see `references/realtime-chat-delivery.md` and `references/chat-message-rendering.md`).
- Link tasks to chat sessions ("Discuss task").

## References
- `references/minimal-dark-ui.css` — clean minimalist dark style defaults to copy into `index.css`.
- `references/pixel-terminal-ui.md` — pixel/terminal/retro variant when explicitly requested.
- `references/ai-workspace-ui-rules.md` — session-specific design and behavior rules.
- `references/hermes-session-resume.md` — exact Hermes state.db workaround.
- `references/file-attachments.md` — file upload/download + prompt injection recipe.
- `references/cron-integration.md` — Hermes cron API wrapper + Kanban task creation.
- `references/cron-jobs-json-parser.md` — reading `~/.hermes/profiles/*/cron/jobs.json` directly because `hermes cron list` only sees the active profile.
- `references/ui-compact-layout.md` — compact 64px agent sidebar + history drawer pattern.
- `references/realtime-chat-delivery.md` — SSE/WebSocket push delivery and thread-safe event-loop routing.
- `references/chat-message-rendering.md` — ChatGPT-style message layout, Markdown typography, typewriter animation.
- `references/session-state-persistence.md` — restoring active profile, session, tab, and history drawer across page reloads.
- `references/aionui-headless-vps.md` — running AionUi WebUI headless on a VPS as an alternative UI.
