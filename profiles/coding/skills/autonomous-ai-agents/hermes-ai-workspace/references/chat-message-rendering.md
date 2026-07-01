# Hermes AI Workspace — message rendering style

ChatGPT-style message formatting for the AI Workspace React UI.

## Layout rule

- **User messages**: right-aligned, inside a rounded gray bubble (`bg-surface-2`, `rounded-2xl`). Keep vertical padding compact (`px-3.5 py-2`) and line-height around `1.55` so user bubbles don't look too tall. Remove any border or glow that was added experimentally.
- **Assistant messages**: left-aligned, on a clean transparent background — no border, no shadow. Exactly like ChatGPT.
- **Font size parity**: set both user-bubble text and assistant Markdown body to the same size, e.g. `text-[15px]`, so the conversation feels visually consistent.

## Typography

Assistant Markdown should use sizes close to ChatGPT's readable body:

| Element | Tailwind classes |
|---------|------------------|
| Body paragraph | `text-[15px] leading-[1.7] mb-4` |
| H1 | `text-[28px] font-bold leading-tight mt-8 mb-5 pb-3 border-b border-border-2` |
| H2 | `text-[22px] font-bold leading-tight mt-7 mb-4` |
| H3 | `text-lg font-bold leading-tight mt-6 mb-3 text-accent` |
| List item | `text-[15px] leading-[1.7]` |
| Inline code | `text-[13px] bg-surface-2 text-accent px-1.5 py-0.5 rounded-md` |
| Blockquote | `text-[15px] leading-[1.7] text-text-dim border-l-[3px] border-accent pl-4 bg-surface-2/30 rounded-r-xl` |
| Table | `text-sm w-full text-left border-collapse` |

## Markdown stack

Use:
- `react-markdown`
- `remark-gfm` (tables, strikethrough, task lists)
- `rehype-highlight` (code blocks — see caveat below)
- `@tailwindcss/typography` plugin for base prose styles
- `highlight.js/styles/atom-one-dark.min.css` for the code theme

### Why `rehype-highlight` alone can show plain white code

`rehype-highlight` does **not** automatically register language grammars. If you just import the theme CSS, fenced code blocks may render as one color because no language is detected/highlighted.

Register languages explicitly and highlight block code manually:

```jsx
import hljs from 'highlight.js'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
// ... import other languages you expect

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('shell', bash)

function CodeBlock({ code, lang }) {
  return (
    <div className="my-3 rounded-2xl border border-border-2 overflow-hidden bg-[#0d0d0d]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161616] border-b border-border-2">
        <span className="text-[11px] text-text-dim uppercase tracking-wider">{lang || 'code'}</span>
        <CopyButton text={code} />
      </div>
      <pre className="p-4 overflow-x-auto">
        <code
          ref={(el) => {
            if (el && code) {
              el.textContent = code
              hljs.highlightElement(el)
            }
          }}
          className="text-[13px] text-[#e2e2e2] leading-relaxed whitespace-pre"
          style={{ fontFamily: "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
        />
      </pre>
    </div>
  )
}
```

Also load a good programming font from Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

And set the UI body font to `Inter`:

```css
body {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
```

## Typewriter animation

If the user asks for ChatGPT-like typing animation:
- Do **not** animate character-by-character — it lags on long responses and fights React re-renders.
- Split the final assistant content by whitespace chunks (`content.split(/(\s+)/)`) and reveal one chunk every ~22 ms.
- Keep the full message already in state; only the *displayed* substring grows.
- Stop the interval once the full text is shown.

## Message copy buttons

Add a small copy icon (no label) below every message that copies the full message text. Use an icon-only button to keep the UI clean; a text label such as "Копировать" adds visual noise.

A copy button that uses `navigator.clipboard.writeText()` will fail silently when the UI is served over plain HTTP (not `localhost` or HTTPS), because the Clipboard API requires a secure context.

Always implement a fallback with `document.execCommand('copy')`:

```jsx
function copyText(text) {
  const ok = () => {
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(ok).catch(() => fallbackCopy())
  } else {
    fallbackCopy()
  }
  function fallbackCopy() {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.focus()
    ta.select()
    try {
      document.execCommand('copy')
      ok()
    } catch (e) {}
    document.body.removeChild(ta)
  }
}
```

Use the same fallback for both per-message copy icons and code-block copy buttons.

## Code blocks

Render fenced code with a copy button and a header showing the language. Keep the existing `CodeBlock` component. Inline code should be subtle, not flashy. Use `rounded-2xl` and comfortable padding (`p-4`) for code blocks.

## "New chat" session title pitfall

The Hermes `state.db` `sessions` table has a `UNIQUE` constraint on `title`. If the UI sends a fixed title such as `NEW_CHAT` for every new session, the second creation will fail with:

```
sqlite3.IntegrityError: UNIQUE constraint failed: sessions.title
```

Fix on the bridge: when the incoming title is `NEW_CHAT`, empty, or missing, generate a unique title with a timestamp:

```python
from datetime import datetime, timezone

title = payload.get("title", "AI Workspace chat")
if title in ("NEW_CHAT", "", None):
    title = f"Новый чат {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')}"
```

## Pitfalls

- Don't put a border or glow around assistant bubbles — it breaks the ChatGPT look.
- Don't use `prose-sm` for assistant text; it makes everything too small and equal-sized.
- Preserve `min-w-0 break-words` on bubbles so long code/URLs don't blow out the layout.
- When the user shares a screenshot of ChatGPT and says "сделай такой же", match sizes/spacing/borders closely rather than approximating. The user expects visual parity.

## References

- `../SKILL.md` — full build instructions.
- `references/ai-workspace-ui-rules.md` — visual style and interaction rules.
- `references/realtime-chat-delivery.md` — how the message arrives instantly.
