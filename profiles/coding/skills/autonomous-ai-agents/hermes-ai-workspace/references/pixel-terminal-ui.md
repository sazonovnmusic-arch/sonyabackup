# Pixel / Terminal / Retro UI style reference

One-shot design system used for the AI Workspace when user requested a minimalist pixel/terminal look.

## CSS variables

```css
:root {
  --bg: #050505;
  --panel: #0a0a0a;
  --panel-2: #0f0f0f;
  --border: #1a1a1a;
  --border-2: #2a2a2a;
  --text: #d0d0d0;
  --text-dim: #666666;
  --accent: #00ff66;
  --accent-2: #a855f7;
  --accent-hover: #00cc55;
  --danger: #ff3333;
}
```

## Fonts

Load both fonts in `index.html`:

```html
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
```

Set body font to `VT323` (the tall, narrow terminal look). Use `Press Start 2P` only for the logo/title.

## Reusable classes

```css
.pixel-box {
  background: var(--panel);
  border: 2px solid var(--border-2);
  box-shadow: 4px 4px 0px var(--border);
}
.pixel-btn {
  background: var(--panel-2);
  border: 2px solid var(--border-2);
  color: var(--text);
  box-shadow: 2px 2px 0px var(--border);
  transition: transform 0.05s, box-shadow 0.05s;
}
.pixel-btn:hover {
  background: var(--panel);
  color: var(--accent);
  border-color: var(--accent);
}
.pixel-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0px 0px 0px var(--border);
}
.pixel-btn-primary {
  background: var(--accent);
  color: var(--bg);
  border: 2px solid var(--accent);
  box-shadow: 2px 2px 0px #004d1a;
}
.pixel-btn-primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}
.pixel-input {
  background: var(--panel);
  border: 2px solid var(--border-2);
  color: var(--text);
  box-shadow: inset 2px 2px 0px #000;
}
```

## UI rules

- No rounded corners (or only `rounded-none` / tiny).
- 2px solid borders everywhere.
- Hard shadows offset by 2–4px for boxes and buttons.
- User messages use purple/accent-2 border; assistant messages use green/accent border.
- Prefix messages with `USER>` / `AGENT>`.
- Status dots are small squares, not circles.
- Use `&gt;` prompt prefix in headings and inputs.
- Blinking cursor effect can be a CSS animation for "AGENT_" typing state.

## Common JSX fragments

```jsx
// Agent sidebar icon
<button className="w-10 h-10 border-2 border-[var(--border)] ...">
  {name.slice(0, 2).toUpperCase()}
</button>

// Chat message bubble
<div className="border-2 px-3 py-2 ..." style={{
  borderColor: m.role === 'user' ? 'var(--accent-2)' : 'var(--accent)'
}}>
  <div className={roleColor}>{m.role === 'user' ? 'USER>' : 'AGENT>'}</div>
  <MessageText content={m.content} />
</div>
```

## Pitfalls

- Pixel fonts are hard to read below 12px; keep body text 16–18px.
- `Press Start 2P` is very wide; use it only for logos, not body text.
- Hard drop shadows can overlap scrollbars; ensure containers have `overflow-y-auto` and enough padding.
