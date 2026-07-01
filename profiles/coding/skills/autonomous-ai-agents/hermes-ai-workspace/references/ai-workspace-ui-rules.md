# Hermes AI Workspace — session-specific design and behavior rules

This file condenses the interaction rules that emerged while building the AI Workspace UI for Никита (Nikita).

## Autonomy rule

When the user asks for a UI feature or fix in the AI Workspace, implement it autonomously. Do not ask for permission before editing the Bridge or UI. Preserve the existing layout and provide complete end-to-end changes (Bridge + UI) for every feature.

## Hermes profile protection rule (hard constraint)

Never delete, drop, truncate, modify, or restart a Hermes profile, its `state.db`, its `cron/jobs.json`, its skills, or its `config.yaml` without explicit user permission. Никита explicitly manages Hermes profile memory and keys himself. The assistant may only touch:

- the custom Bridge code (`~/ai-workspace/bridge/`)
- the custom UI code (`~/ai-workspace/ui/`)
- the Bridge-only `workspace.db`

Before large experiments, back up `~/ai-workspace/ui/` and `~/ai-workspace/bridge/`.

## Visual style

- Near-black background (`#0a0a0a`).
- Sky-blue accent (`#0ea5e9`).
- Strong rounding everywhere: buttons/inputs/cards `rounded-lg`–`rounded-2xl`; message bubbles `rounded-3xl` with one less-rounded tail corner.
- Profile avatars stay **square-ish with soft rounding**, not circular.
- System sans-serif, thin 1px borders.
- Session list items are borderless; active state uses subtle background, hover uses hover background.

## Welcome screen

- Heading: `На связи {profile}, чем могу помочь?`
- Centered input below.
- Replace any generic "AI" logo with the **selected profile's initials or avatar**.
- PNG icons supplied later by the user take precedence over initials.

## History drawer

- Slide-in from the left; it **pushes** the chat area, not overlays it.
- Stays open after selecting a session; only closes via explicit close button or burger toggle.
- Session blocks: start compact, then iterate to medium size based on feedback.

### "New chat" semantics

- The **+ Новый чат** button should not immediately create a server session. It should only clear the current selection and show the welcome-screen composer.
- The actual `sessions` row is created on first message send.

## Chat behavior

- Push new assistant messages via SSE/WebSocket with thread-safe event-loop routing.
- Poll only as fallback.
- Load full conversation history when opening a session; paginate very large sessions.
- Use ChatGPT-style rendering: user messages in a compact gray bubble, assistant on a plain background, both at the same font size.

### Typewriter animation

Only add a typewriter effect if the user explicitly asks. When added, animate by whitespace chunks (~22 ms), not character-by-character, to avoid lag on long replies.

## Status tab

- Dropdown menus start closed.
- Auto-refresh status every ~5 seconds.
- Use `profile` field from API for identity, never assume a `name` field.

## Evaluating third-party UI solutions

When the user proposes third-party Hermes dashboards (AionUi, ClawFleet, etc.):

1. Inspect the repo structure and build requirements quickly.
2. If it requires heavy Electron builds, custom backends, or Docker fleets that don't map to the existing Hermes CLI profiles, recommend borrowing mechanics only rather than replacing the custom UI.
3. Do not spend long trying to build third-party Electron apps on the VPS if they hang or require many native dependencies.
4. Borrow ideas: push delivery, status card layout, session-list patterns — then implement them in the custom UI/Bridge.

## References

- `../SKILL.md` — full build instructions and architecture.
- `references/realtime-chat-delivery.md` — SSE/WebSocket delivery mechanics.
- `references/ui-roundness-and-profile-avatar.md` — exact rounding and avatar rules.
- `references/chat-message-rendering.md` — ChatGPT-style message layout and typography.
- `references/session-state-persistence.md` — restoring state across page reloads.
