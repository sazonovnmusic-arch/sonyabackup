---
name: hermes-bridge-workspace-ui
description: "Build web control panels and bridge APIs on top of Hermes Agent profiles. Covers reading state.db, creating resumable sessions, invoking hermes CLI as a backend, and building React dashboards for agent chat, kanban, and status."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, bridge-api, workspace-ui, control-center, agents, fastapi, react, kanban]
    related_skills: [hermes-agent, plan, systematic-debugging]
---

# Hermes Bridge + Workspace UI

Use this skill when building a web-layer control center over Hermes Agent — dashboards where users pick an agent, chat with it, manage tasks, and observe agent status without opening Telegram or a terminal.

**Key constraints learned from this workspace:**
- Assistant messages are rendered as structured Markdown; user messages stay as plain text bubbles (ChatGPT-style).
- UI must use strong rounded corners, sky-blue accent (`#0ea5e9`), near-black background, and squarish profile avatars.
- Live chat delivery uses WebSocket with SSE fallback; SSE is the safer default because browser-automation proxies often close raw WebSocket.
- Push notifications from the Hermes background task must be scheduled on the main uvicorn loop via `run_coroutine_threadsafe`.
- Never modify Hermes profiles, `state.db`, cron configs, or skills without explicit permission.

## What this skill covers

- Hermes Bridge API (FastAPI) that wraps the Hermes CLI and reads Hermes SQLite state.
- Creating Hermes sessions that can be resumed by `hermes chat --resume`.
- Sending messages to an agent from a web UI and reading the response back.
- Building a React workspace with agent directory, ChatGPT-like chat, Kanban board, and agent status dashboard.

## What it does NOT cover

- Replacing Hermes Core (memory, gateway, model routing).
- Authentication / multi-tenant isolation.

## When to use WebSocket vs polling

Start with **WebSocket** for chat delivery (see `references/websocket-chat-pattern.md` and `references/realtime-chat-delivery.md`). It eliminates the 500 ms polling delay and the "refresh to see the answer" behavior.

Because some browser automation proxies and load balancers block or mishandle WebSocket, always provide **Server-Sent Events (SSE)** as a fallback (`references/realtime-chat-delivery.md`). SSE works over plain HTTP, auto-reconnects in most browsers, and is easier to proxy. Keep the polling endpoint from `references/chat-polling-patterns.md` as the final fallback.

### Thread-safe push from a background Hermes task

Hermes itself runs chat in a background thread with its own event loop. If the Bridge tries to push a new message to WebSocket/SSE clients using `asyncio.run()` from that thread, it will usually fail because a loop is already running. The fix:

1. Capture the main uvicorn loop on startup:
   ```python
   _main_loop: asyncio.AbstractEventLoop | None = None

   @app.on_event("startup")
   def _store_main_loop():
       global _main_loop
       try:
           _main_loop = asyncio.get_running_loop()
       except RuntimeError:
           _main_loop = None
   ```
2. From the background thread, schedule the coroutine on the main loop:
   ```python
   def _notify_from_thread(session_id: str, payload: dict):
       if _main_loop and _main_loop.is_running():
           asyncio.run_coroutine_threadsafe(_notify_all(session_id, payload), _main_loop)
   ```
3. Call `_notify_from_thread(...)` whenever Hermes writes the assistant message to `state.db`.

Without this, the UI only sees the response after a manual page refresh, even though the message is already in the database.

## Cron job discovery and control

Hermes stores cron jobs per profile in:

```
~/.hermes/profiles/<profile>/cron/jobs.json
```

Each file contains `{ "jobs": [ ... ] }`. Do **not** rely on `hermes cron list` to enumerate jobs for all profiles — that command only sees the currently active profile. Instead, read each profile's `jobs.json` directly.

A parsed job entry looks like:

| Field | Meaning |
|-------|---------|
| `id` | Short hex job id |
| `name` | Human name |
| `prompt` / `script` | What the agent runs |
| `schedule.display` / `schedule.expr` | Cron expression or "once at ..." |
| `enabled` | Whether the job is enabled |
| `state` | e.g. `scheduled`, `paused` |
| `last_run_at` | ISO timestamp |
| `next_run_at` | ISO timestamp |

Expose these through the Bridge as `GET /api/cron` with a `profile` filter, and support `POST /api/cron/{id}/{run|pause|resume}` and `DELETE /api/cron/{id}`. Hermes CLI commands `hermes --profile <name> cron <subcommand> <id>` operate on the owning profile, so the Bridge must remember which profile each job belongs to.

Cron jobs can spawn Kanban tasks via `POST /api/cron/{id}/tasks` — create a TODO task titled after the cron job and optionally link `cronjob_id`.

## File attachments in chat

Hermes CLI does not accept arbitrary `--file`, but it supports `--image` for vision models. Build a two-path attachment system:

| File type | How it reaches the agent |
|-----------|--------------------------|
| Text files (`.txt`, `.md`, `.json`, `.yaml`, `.csv`, code) | Upload to `files/<profile>/<session>/`, read content, prepend to the prompt with a `[Attached file: ...]` marker. |
| Images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`) | Upload and pass the file path via `hermes chat --image <path> --resume <session> -q "..."`. |

Store uploads outside Hermes' own directories, e.g. `bridge/files/<profile>/<session>/`, and expose them at `/api/sessions/<profile>/<session>/files/<name>` for download. Return file metadata (name, size, mime, `is_image`, `is_text`) so the UI can render or toggle attachments before sending.

## Compact responsive layout

A dense workspace UI should maximize chat/content area:

1. **Agent sidebar** — collapse to a 64px icon strip showing **squarish avatars** (`w-10 h-10`, modest rounding like `rounded-md` / 10–16px) with initials and a tooltip. Do **not** make profile avatars circular unless explicitly requested. The small "AI" logo at the top uses the same rounded style.
2. **Session history** — hide in a slide-out drawer. Open it with a header burger button. The drawer must **slide in from the left and push the chat area to the right**, not overlay it. Implementation:
   - Drawer: `absolute left-0 top-0 bottom-0 w-64 z-20 transition-transform duration-200`, classes `translate-x-0` when open, `-translate-x-full` when closed.
   - Chat container: sibling div with `transition-[margin] duration-200`, receives `ml-64` when drawer is open.
   - The drawer **stays open** after the user clicks a session; only close it when the user clicks the ✕ button or the burger again.
3. **Session list items** — compact (roughly half the original height), **borderless**. Use only hover background (`hover:bg-[var(--surface-2)]`) and active-state background/text color. Small dim secondary text for date + message count.
4. **Header toggle** — the same burger button should highlight (accent border/text) when the drawer is open. Keep a close button (`×`) inside the drawer header for discoverability.
5. **Tabs** — keep Chat / Kanban / Cron / Status as compact pill buttons in the top bar, not a separate sidebar section.
6. **Welcome screen** — when no session is selected, show a centered squarish profile avatar with initials, heading `На связи {profile}, чем могу помочь?`, and a rounded centered input. Do not show a bottom composer until a session is active.
7. **Profile icon over generic AI logo** — replace a generic "AI" logo in the welcome screen with the selected profile's initials. When the user later supplies PNG icons, swap the initials for the image.

## Status tab agent actions

Each agent card has a 3-dot menu in the top-right corner:

- Hover: gray highlight.
- Click: dropdown with `Перезапустить`, `Остановить`, `Запустить`, `Удалить`.
- **Dropdown must be closed by default.** The API returns `profile`, not `name`; the UI state must compare `menuAgent?.profile === a.profile`, otherwise `undefined === undefined` opens every menu at once.
- Any action opens a centered confirmation modal before executing.
- Backend endpoints:
  - `POST /api/agents/{profile}/restart`
  - `POST /api/agents/{profile}/start`
  - `POST /api/agents/{profile}/stop`
  - `POST /api/agents/{profile}/delete` — safe default: clear the profile's sessions/messages from `state.db`, do **not** delete the profile directory unless explicitly requested.
- After the action, refresh `/api/agents/status` and re-render the cards.

## Creating profiles from the UI

Add a `+` button at the bottom of the agent sidebar that opens a modal:

- Profile name (alphanumeric, `_`, `-`).
- Provider: select from known providers (`ollama-cloud`, `openrouter`, `openai`, `anthropic`, `openmodel`) plus a **Custom** option that reveals a free-text provider field.
- Model, e.g. `kimi-k2.6:cloud`.
- System / "врождённый" prompt textarea describing the agent's role.
- Optional API key and Base URL.
- Backend: `POST /api/profiles` creates the profile directory, writes `config.yaml` with model/provider/base_url, writes `.env` with the provider's API key env var if a key is supplied, and returns the new profile.

After creation, select the new profile and switch to the Chat tab so the user can start a session immediately.

## Agent action safety rule

**Never modify, delete, drop, truncate, or restart a Hermes profile, its `state.db`, its cron configs, its skills, or its `config.yaml` without explicit user permission.** This is a hard rule for this workspace. The user has explicitly forbidden the assistant from touching Hermes profile data.

When a status-card menu has a `Удалить` (Delete) option, the backend action can remove the entire `~/.hermes/profiles/<name>` directory including `config.yaml`, `.env`, `state.db`, and `gateway.pid`. Safe defaults:

- The `Удалить` action should **clear the profile's sessions/messages only**, not remove the directory.
- If the user explicitly demands full directory deletion, confirm the exact profile name, back up the remaining files, and either let the user execute it themselves or use a throwaway test profile for verification.
- **Never run `curl -X POST /api/agents/{name}/delete` or similar destructive endpoints yourself during development.** Use a throwaway profile for any QA of destructive flows.
- Backup the custom UI and Bridge before large experiments (`~/ai-workspace/ui_backup/`, `~/ai-workspace/bridge_backup/`).

## Core architecture

```
React UI  ──▶  FastAPI Bridge  ──▶  Hermes CLI  ──▶  ~/.hermes/profiles/<profile>/state.db
                                    └── LLM / tools / memory
```

The Bridge lives between the browser and Hermes. It does not reimplement Hermes — it translates HTTP requests into Hermes CLI invocations and reads Hermes' SQLite session store.

## Discovery: where Hermes keeps state

| Data | Location |
|------|----------|
| Profiles | `~/.hermes/profiles/<name>/` |
| Default profile config | `~/.hermes/config.yaml` (fallback only) |
| Sessions & messages | `~/.hermes/profiles/<name>/state.db` |
| Gateway pid/lock | `~/.hermes/profiles/<name>/gateway.pid` |

Read profiles by scanning `~/.hermes/profiles/` and reading `config.yaml` in each directory. Do **not** rely on `HERMES_HOME` env var when the Bridge must see all profiles — the running Hermes process sets it to the active profile directory.

## Creating a resumable Hermes session

Hermes `chat --resume SESSION_ID` only recognizes sessions that look like Hermes-native sessions. A minimal INSERT into `state.db` must include:

- `id` — format Hermes expects: `YYYYMMDD_HHMMSS_xxxxxx` (hex suffix).
- `source` — e.g. `'api'`.
- `model` — the default model name from the profile config.
- `system_prompt` — at minimum the Hermes Agent Persona block (can be short).
- `billing_provider` — provider slug, e.g. `'ollama-cloud'`.
- `billing_base_url` — provider base URL, e.g. `'https://ollama.com/v1'`.
- `estimated_cost_usd`, `cost_status`, `cost_source` — default to `0.0`, `'unknown'`, `'none'`.
- `title` — human-readable.
- `started_at`, `message_count=0`.

Create the session **empty** (no messages). Then send the first user message via `hermes chat -q "..." --resume SESSION_ID`. Hermes will write both the user message and the assistant response into the session.

If you pre-insert a `user` message before calling `--resume`, Hermes will duplicate it and you will see two identical user messages in the chat history.

## Sending a message

```python
subprocess.run([
    "hermes", "--profile", profile_name,
    "chat", "-q", user_message,
    "--resume", session_id,
    "--source", "api",
], capture_output=True, text=True, timeout=300)
```

After the command returns, read the latest `assistant` message from the profile's `state.db` and return it to the UI.

## Reading messages

```sql
SELECT id, role, content, timestamp, active
FROM messages
WHERE session_id = ? AND active = 1
ORDER BY timestamp ASC
```

Filter to `role IN ('user', 'assistant')` for a clean chat view.

## Computing agent status

Hermes has no native status field. Derive it from `state.db` activity for `source='api'` sessions:

| Status | Rule |
|--------|------|
| `waiting` | Last message is `user` and within last 5 minutes. |
| `working` | Last message is `assistant` (or any message) within last 5 minutes. |
| `idle` | Last activity older than 5 minutes. |
| `offline` | Gateway pid/lock indicates the profile's gateway is not running. |

Adjust thresholds to taste. Store optional overrides in a Bridge-only `workspace.db` if the UI needs manually-set statuses.

## Workspace DB (Bridge-only)

Keep tasks, manual status overrides, and other UI state in a separate SQLite file (e.g. `bridge/workspace.db`), not inside Hermes' `state.db`. Schema example:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo',
    assignee_profile TEXT,
    session_id TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
```

## React UI structure

A compact workspace UI has:

1. **Sidebar** — agent directory + bottom navigation (Chat / Kanban / Status).
2. **Chat view** — session list + message stream + composer.
3. **Kanban view** — three columns (todo / in_progress / done) with task cards and assignee selector.
4. **Status view** — agent status cards with model, gateway state, and last activity.

Use Tailwind or similar for quick dark-themed layout. Vite is fine for MVP; migrate to Next.js later if SSR/routing is needed.

## Common pitfalls

1. **Relying on `HERMES_HOME` for profile discovery.** When running inside a Hermes session, this env var points at the active profile, not `~/.hermes`. Use `Path.home() / '.hermes'` for the Bridge.

2. **Assuming the production UI server proxies `/api` to the Bridge.** `vite dev` can proxy `/api` via `vite.config.js`, but `npx serve -s dist -l 3000` only serves static files. If the React app uses a relative API base such as `const API = '/api'`, production requests will hit port 3000 and 404, leaving the agent list empty and the UI stuck on "Выберите агента". Fix: use an absolute API base in the built app, e.g. `const API = 'http://<bridge-host>:8123/api'`, or put an nginx reverse proxy in front of both. See `references/production-ui-deploy.md` for the exact command sequence.

3. **Using the raw `>` character inside JSX content.** Text like `<div>>_</div>` confuses the JSX parser because `>` is interpreted as a closing tag. Write `&gt;_` or wrap the character in an expression `{ '>' }`.

2. **Creating sessions without `system_prompt`/`model`/`billing_provider`.** Hermes `--resume` will say "Session not found" or silently fail.

3. **Pre-inserting the user message before invoking Hermes.** This causes duplicated user messages. Create the session empty and pass the message through `hermes chat -q`.

4. **Parsing Hermes stdout for the assistant response.** Hermes prints banners and formatting. Always read the actual `assistant` row from `state.db`.

5. **Forgetting that each profile has its own `state.db`.** Session IDs are unique per profile, but queries must use the correct profile's DB.

6. **Returning full chat history to the browser.** Hermes sessions can grow to hundreds of large messages. Always paginate the messages endpoint and let the UI request pages, or the browser will freeze and the composer/header may disappear. See `references/chat-ui-performance-patterns.md`.

8. **Scanning every message to compute agent status.** Queries like `SUM(CASE WHEN role='assistant' ...)` over the entire `messages` table read all large message bodies and make the Status tab lag. Use `ORDER BY timestamp DESC LIMIT 1` plus an index on `(session_id, active, timestamp)`, and cache the result for a few seconds. See `references/chat-ui-performance-patterns.md` for the exact helper.

10. **Broken chat polling.** The naive "return the last assistant message" endpoint misses multi-step Hermes outputs (empty assistant → tool → final), and polling every 2 seconds feels laggy. Use `after_id` to stream all new assistant messages, poll every 500 ms, and display responses whole — do not animate them character-by-character. Prefer WebSocket over polling: push messages from the Bridge as soon as Hermes writes them to `state.db`. See `references/websocket-chat-pattern.md` (primary) and `references/chat-polling-patterns.md` (fallback).

10. **Writing line-numbered file output back to source files.** Hermes `read_file` can return lines prefixed with `1|`, `2|`, etc. Writing that directly into a JSX/JS file produces a syntax error and a blank white screen. Always regenerate large files from a clean string via `write_file` or `execute_code`; for partial patches, strip the prefix with a regex or run `scripts/fix-line-number-corruption.py` before rebuilding.

9. **Testing destructive agent actions against live user profiles.** When implementing `Удалить` / `delete` for an agent card, never verify it by calling the endpoint on a real profile. A destructive backend action can remove `config.yaml`, `.env`, `state.db`, and the entire profile directory. Safe verification paths:
   - Point the test at a throwaway profile you create first.
   - Or make the `delete` action non-destructive by default (clear sessions/messages only), and require an explicit flag or separate admin call to remove the directory.
   - If the user explicitly demands full profile deletion, confirm the exact profile name and back up its remaining files before executing. Never run `curl -X POST /api/agents/{name}/delete` yourself during development.

10. **Blank page after `npm run build`.** If `curl` returns correct `index.html` and JS/CSS load with HTTP 200, but `#root` remains empty, the bundled React app is crashing during initialization. Common causes after patching:
   - A `useState` declaration was accidentally removed while moving/reordering hooks (e.g. `const [messages, setMessages] = useState([])`).
   - An unescaped `>` or `<` character in JSX.
   - Line-number corruption from `read_file` output written back into a source file.
   - A `useEffect` that opens `EventSource` or `WebSocket` throws synchronously before first paint.
   - Diagnose by checking the browser console for the first thrown error, or by running `npx vite build` and inspecting the produced `dist/assets/*.js` for syntax errors. See `scripts/verify-ui-render.sh` for a quick probe and `references/react-patching-and-blank-page.md` for the full recovery guide.

## History session list sizing

Getting the session list "just right" usually takes 2–3 iterations with this user. The pattern that works is:

1. Start compact: `px-3 py-2`, title `text-sm`, date `text-xs`, `space-y-1.5`. This is the safe default.
2. If the user says "make headers bigger", increase the **whole block**, not just the font: `px-4 py-3.5`, title `text-base`, `space-y-3`, `rounded-lg`. Then ask for visual feedback.
3. If the user then says "too big", dial back to a medium size: `px-3 py-2.5`, title `text-sm`, `space-y-2`. That midpoint is what usually sticks.

Avoid jumping straight to very large blocks. The user reacts to proportion more than to absolute font size.

## Rendering agent responses as Markdown

Agent answers in Hermes are plain text that often contains Markdown (headers, lists, code blocks, tables, quotes). Render assistant messages with a Markdown parser so they appear structured, while keeping user messages as plain text bubbles (ChatGPT-style).

- Markdown rendering stack: `react-markdown`, `remark-gfm`, `rehype-highlight`, `@tailwindcss/typography`.
- Use `Inter` for UI text, `Fira Code` for code, and `atom-one-dark` highlight.js theme for a Sublime-like look.
- ChatGPT-style sizing: H1 28px, H2 22px, H3 18px (accent color), body 15px with 1.7 line height.
- User message bubble: same 15px font, compact padding, `leading-[1.55]` to keep height low.
- Add a word-by-word typewriter effect for assistant messages instead of character-by-character to avoid UI lag.
- Add a copy icon (16×16) below every message with `navigator.clipboard` + `document.execCommand` fallback for HTTP contexts.
- Do **not** put a border, glow, or background box around the whole assistant message.

Full component recipes, exact Tailwind classes, and the copy/typewriter code are in `references/agent-message-markdown-rendering.md`.

## UI design notes

For this workspace the settled visual style is a minimal dark theme:

- Background near-black (`#0a0a0a`), surfaces at `#111111`/`#161616`/`#1f1f1f`.
- Sky-blue accent (`#0ea5e9`).
- **Strong rounding everywhere** — buttons/inputs/cards use `rounded-lg`–`rounded-2xl`; message bubbles use `rounded-3xl` with one less-rounded "tail" corner (`rounded-br-md` for user, `rounded-bl-md` for assistant). See `references/ui-roundness-and-profile-avatar.md` for the exact scale.
- **Profile avatars stay squarish** (`rounded-md`/`rounded-xl`), not circular.
- The generic "AI" badge in the welcome screen should be replaced with the **selected profile's initials or avatar**. See `references/ui-roundness-and-profile-avatar.md`.
- System sans-serif font, thin 1px borders.

Pixel/retro arcade styles should only be used when explicitly requested, and reverted promptly if the user finds them too arcade. See `references/design-iteration-notes.md` for the full design rules and `references/chat-ui-performance-patterns.md` for layout/performance rules.

## Quick start scaffold

```bash
mkdir -p ~/ai-workspace/bridge ~/ai-workspace/ui/src
cd ~/ai-workspace/bridge
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn[standard] pydantic pyyaml python-multipart

cd ~/ai-workspace/ui
npm create vite@latest . -- --template react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## Verification checklist

- [ ] Bridge lists all Hermes profiles correctly.
- [ ] Creating a session via Bridge produces a session resumable by `hermes chat --resume`.
- [ ] Sending a message writes exactly one user row and one assistant row in `state.db`.
- [ ] UI chat shows the full conversation history.
- [ ] Kanban tasks can be created, assigned to agents, and moved between columns.
- [ ] Status dashboard reflects idle/working/waiting/offline based on real activity.

## References

- `references/bridge-session-insert-recipe.md` — exact SQL and pitfalls for creating Hermes-resumable sessions from a Bridge API.
- `references/hermes-cron-jobs-json.md` — exact `jobs.json` schema and mapping for cross-profile cron discovery.
- `references/chat-ui-performance-patterns.md` — how to handle very long Hermes sessions: server-side pagination, message collapsing, fixed-height layout, and avoiding first-session auto-load.
- `references/chat-polling-patterns.md` — reliable polling for assistant responses, avoiding duplicated user messages and typewriter-related render stalls.
- `references/chat-delivery-race-conditions.md` — reliable push delivery when Hermes finishes before the UI opens SSE/WebSocket; catch-up on connect, retry notify, and polling fallback.
- `references/design-iteration-notes.md` — settled dark/minimal UI style, drawer behavior, welcome screen copy, and iteration rules.
- `references/history-session-list-sizing.md` — proven iteration pattern for getting the session list block size right.
- `references/session-history-bubble-to-top.md` — move the active session to the top of the history list immediately on send, with a smooth CSS animation.
- `references/new-chat-unique-title.md` — why the "New chat" button stops working after the first click due to a UNIQUE title constraint and how to fix it.
- `references/agent-message-markdown-rendering.md` — render assistant messages as structured Markdown (ChatGPT-style sizing, typewriter, copy icon, code blocks) while keeping user messages as plain text bubbles.
- `references/ui-roundness-and-profile-avatar.md` — settled rounding scale and replacing the generic AI logo with the selected profile's initials/avatar.
- `references/websocket-chat-pattern.md` — push new assistant messages instantly via WebSocket, with polling fallback.
- `references/realtime-chat-delivery.md` — WebSocket + SSE combined implementation, including the thread-safe event-loop notify fix and why SSE is the safer default in browser-automation environments.
- `references/ui-roundness-and-profile-avatar.md` — settled rounding scale and replacing the generic AI logo with the selected profile's initials/avatar.
- `references/react-patching-and-blank-page.md` — why the UI renders an empty `#root` after patching and how to recover (lost `useState`, unescaped JSX characters, EventSource throws, line-number corruption).
- `references/agent-message-markdown-rendering.md` — render assistant messages as structured Markdown (ChatGPT-style sizing, typewriter, copy icon, code blocks) while keeping user messages as plain text bubbles.
- `scripts/verify-ui-render.sh` — quick probe to distinguish a server outage from a JS runtime crash that leaves `#root` empty.
- `scripts/fix-line-number-corruption.py` — utility to strip `1|`, `2|` prefixes from files corrupted by accidental line-number writes.

## Future work
- Persist agent status overrides.
- Link tasks to chat sessions so "Discuss task" opens a contextual session.
