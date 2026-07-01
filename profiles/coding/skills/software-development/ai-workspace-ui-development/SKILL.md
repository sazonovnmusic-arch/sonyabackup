---
name: ai-workspace-ui-development
description: Build or extend the user's AI Workspace UI (React + FastAPI bridge) with the correct dark ChatGPT-like design system, state persistence rules, and safe deployment practices.
trigger: User asks to add, fix, extend, redesign, or debug features in ~/ai-workspace UI or bridge. Also applies when borrowing mechanics from third-party tools (AionUi, ClawFleet, etc.) for this project.
---

# AI Workspace UI Development

Build and extend the user's AI Workspace — a ChatGPT-style dark UI + FastAPI bridge over Hermes Agent.

## Design system (non-negotiable)
- Background: `#0a0a0a` near-black.
- Accent: sky-blue `#0ea5e9` (not green, not purple).
- Strong rounding: inputs/buttons `rounded-2xl`, large cards `rounded-3xl`/CSS vars `--radius-md: 22px`, `--radius-lg: 32px`, `--radius-xl: 48px`.
- Compact dark sidebar: agent profiles shown as square-ish rounded avatars (icon or initials). No pixel/arcade look.
- Chat layout: user messages in subtle gray bubble; assistant messages on clean background, optionally with a light border/bubble.
- Code blocks: Fira Code + highlight.js Atom One Dark, explicit language registration.
- Welcome line: `На связи {profile}, чем могу помочь?` with the selected profile's avatar/initials where the AI icon usually sits.
- History drawer pushes chat content (margin-left animation), stays open until manually closed. Selecting a session or pressing "New chat" must NOT close it.
- 16×16 copy icon below every message.

## Architecture
- `~/ai-workspace/bridge/main.py` — FastAPI, SSE events, WebSocket, session CRUD, file upload.
- `~/ai-workspace/ui/src/App.jsx` — single-file React app with Tailwind.
- `~/ai-workspace/ui/src/App.css` — CSS vars for radii, colors, surfaces.
- Production UI served by `npx serve -s dist -l 3000`.
- Bridge served by `.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8123 --log-level info`.

## Standard workflow
1. Read current `App.jsx`, `App.css`, and `bridge/main.py` before editing.
2. Make end-to-end changes: bridge endpoint + UI consumption together. Do not leave half-integrated features.
3. Build: `cd ui && npm run build`.
4. Restart `serve` to pick up new `dist/` (browser caches aggressively).
5. Verify via browser; if black screen or undefined function, check console and the prop/state mismatch pitfall below.
6. Preserve existing CSS classes on forms (`formFb__inputs`, `ss`, `pp`, `formFb__btn`) where relevant.

## State persistence rules
- Use `localStorage` for durable UI state (selected profile, active session per profile, history open/closed).
- Keep the state shape in sync between `App` and `ChatView` via props; never let a child component reference a setter it does not receive.
- On page load, restore profile → active session for that profile → history open state.

## "New chat" behavior
- Button must NOT create a session immediately.
- It only clears the active session, messages, and input, showing the centered welcome input.
- A session is created only when the user sends the first message.

## Common pitfalls
- **Black screen after build**: usually a missing React state variable or a prop used but not declared in the component signature. See `references/react-prop-state-mismatch.md`.
- **Stale UI after rebuild**: `npx serve` may cache old `dist/`. Kill and restart the process, then hard-refresh browser.
- **SSE not delivering messages**: ensure `_notify_all` uses `run_coroutine_threadsafe` into the main uvicorn loop; add catch-up broadcast for newly connected clients.
- **History not staying open**: verify drawer state is controlled only by its own close button and `localStorage`, not by session selection.

## When to borrow vs build
If the user wants to integrate a third-party agent UI (AionUi, ClawFleet, etc.):
1. Check whether Hermes is supported natively (AionUi uses ACP; Hermes has `hermes acp`).
2. Prefer a quick headless deploy test before committing to migration.
3. Compare resource cost (Electron headless needs Xvfb and more RAM) against the value of a polished UI.
4. Keep the existing `~/ai-workspace` archive safe before any migration.

## Archiving / restoring
Before large experiments or pauses, package the project:
- Stop bridge and UI processes.
- `tar --exclude='ui/node_modules' --exclude='bridge/.venv' --exclude='ui/dist' -czf ai-workspace-YYYYMMDD-HHMMSS.tar.gz ai-workspace`
- Write `README-STATE.md` and a `restore.sh`.
See `references/archive-restore-pattern.md`.

## References
- `references/design-system.md` — condensed visual rules.
- `references/react-prop-state-mismatch.md` — the `setActiveSessionIds is not defined` case study.
- `references/archive-restore-pattern.md` — packaging and restore recipe.
