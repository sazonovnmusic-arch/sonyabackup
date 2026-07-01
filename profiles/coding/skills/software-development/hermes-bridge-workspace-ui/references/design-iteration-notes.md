# AI Workspace UI: design iteration notes

Session-derived conventions for the AI Workspace React UI at `~/ai-workspace/ui`.

## Settled visual style

- **Background**: near-black `#0a0a0a`.
- **Surfaces**: `#111111`, `#161616`, `#1f1f1f`.
- **Borders**: 1px, `#222222` / `#2a2a2a`.
- **Accent**: sky-blue `#0ea5e9`.
- **Text**: `#f0f0f0`, dim `#808080`.
- **Font**: system sans-serif, 14px base.
- **Corners**: rounded, but **not uniform**:
  - Buttons / inputs / cards / Kanban columns / Cron cards: `rounded-lg` (16px) to `rounded-2xl` (24px).
  - Messages: `rounded-3xl` with one "tail" corner kept slightly less rounded (`rounded-br-md` / `rounded-bl-md`).
  - **Profile avatars in sidebar**: stay squarish (`w-10 h-10`) with modest rounding (`rounded-md`, ~10–16px). Do **not** make them circular unless explicitly asked.
  - **Scrollbar thumb**: rounded-full.

## Welcome screen

When no session is active, center:

1. A squarish avatar with the selected profile's initials (`name.slice(0,2).toUpperCase()`).
2. Heading: `На связи {profile}, чем могу помочь?`.
3. Subtext: `Напишите сообщение ниже.`
4. A rounded, pill-like input with attach and send buttons.

Do **not** show a bottom composer on the welcome screen.

## Copying a reference screenshot

When the user attaches a screenshot and says "сделай такой же" / "like ChatGPT":

1. Do **not** ask clarifying questions about every detail. Extract the obvious structural rules from the image and apply them.
2. Common ChatGPT rules we use:
   - **User messages** live in a subtle filled bubble (`bg-[var(--surface-2)]`) with compact padding.
   - **Assistant messages** sit on the clean background, no border, no glow, no extra box.
   - Text size is the **same** on both sides (`text-[15px]`).
   - Reduce user bubble height with `leading-[1.55]` if asked.
   - Assistant content is rendered as Markdown with ChatGPT-style hierarchy (H1 28px, H2 22px, H3 accent 18px, body 15px/1.7).
3. If the user pushes back ("не обязательно" / "too much"), strip the extra decoration and return to the structural layout from the screenshot.
4. Iterate visually: build, show, adjust. The user prefers autonomous changes without permission prompts.

## Session history drawer

- Opens with a header burger button ☰ (same button toggles open/close).
- Slides in from the left with `transition-transform duration-200`.
- The **chat area must shrink**, not be overlaid. Use an absolute-positioned drawer (`left-0 top-0 bottom-0 w-64`) and give the sibling chat container `ml-64` via `transition-[margin]` when open.
- The drawer should **stay open** after the user clicks a session; only close when the user clicks ✕ or the burger again.
- Session items in the list should be **compact** (~half the original height) and **borderless**. Use only a hover background (`hover:bg-[var(--surface-2)]`) and an active-state background/text color. No borders.

## Status tab agent cards

Each card gets a 3-dot menu in the top-right corner:

- Hover: gray highlight.
- Click: dropdown with `Перезапустить`, `Остановить`, `Запустить`, `Удалить`.
- Choosing an action opens a centered confirmation modal before calling `POST /api/agents/{profile}/{restart|start|stop|delete}`.
- After the action, refresh `/api/agents/status`.

## What to avoid

- Pixel/arcade/retro styles unless the user explicitly asks for them; revert quickly if the user calls them "too arcade".
- Generic "AI" logo in the welcome screen; use the selected profile's initials (and later PNG icons when supplied).
- Centered bottom hint like "Откройте историю или напишите сообщение ниже." — keep copy minimal.

## Design iteration workflow

The user prefers **autonomous iteration**: make end-to-end Bridge + UI changes without asking permission, then show the result. When the user says "make it more X / replace Y with Z", apply the change across both backend and frontend if needed, build the UI, and verify visually.
