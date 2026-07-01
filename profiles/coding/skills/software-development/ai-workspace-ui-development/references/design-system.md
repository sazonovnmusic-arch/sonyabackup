# AI Workspace Design System

Condensed rules from user feedback. Follow exactly unless the user overrides.

## Palette
- Background: `#0a0a0a`
- Surface: `#111111` / `#161616`
- Surface-2: `#1a1a1a`
- Border: `#2a2a2a`
- Border-2: `#333333`
- Text: `#e2e2e2`
- Text dim: `#9ca3af`
- Accent: `#0ea5e9` (sky-blue)
- Danger: `#ef4444`

## Radii
Prefer CSS variables in App.css:
- `--radius-md: 22px`
- `--radius-lg: 32px`
- `--radius-xl: 48px`

Apply via inline `style={{ borderRadius: 'var(--radius-lg)' }}` or Tailwind `rounded-2xl` for smaller elements.

## Layout
- Left sidebar: 64px wide, profile avatars/icons only.
- Top header: 48px, tabs (Chat, Kanban, Cron, Status).
- History drawer: 256px, pushes chat, stays open until manually closed.
- Input: centered when no session; bottom-fixed when session active.

## Chat
- User messages: gray bubble (`bg-[var(--surface-2)]`), `rounded-2xl rounded-br-md`.
- Agent messages: plain dark background with subtle border if needed.
- Font size: 15px both roles.
- Line height: 1.55–1.7.
- Copy icon 16×16 below each message.
- Welcome icon: selected profile's initials/avatar, not generic AI icon.

## Code
- Font: Fira Code, ui-monospace fallback.
- Theme: highlight.js Atom One Dark.
- Explicitly register languages: js, python, bash, sql, json, yaml, html, css, typescript, go, rust, php, dockerfile.
