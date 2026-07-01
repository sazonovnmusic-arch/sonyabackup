# Markdown rendering for agent messages

Reference: how to render Hermes assistant responses as structured Markdown in the AI Workspace React UI while keeping user messages as plain text bubbles.

## Stack

```bash
cd ~/ai-workspace/ui
npm install react-markdown remark-gfm rehype-highlight
npm install -D @tailwindcss/typography
```

- `react-markdown` — core renderer.
- `remark-gfm` — GitHub-flavored Markdown (tables, task lists, strikethrough).
- `rehype-highlight` — fenced code block syntax highlighting.
- `@tailwindcss/typography` — `prose` defaults for dark mode.

## Fonts

Add good fonts to `index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Set `Inter` for UI text in `index.css` and `Fira Code` for code:

```css
body {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
```

```jsx
<code style={{ fontFamily: "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}>
```

## Tailwind config

```js
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: { extend: {} },
  plugins: [require('@tailwindcss/typography')],
}
```

## Imports

```jsx
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/atom-one-dark.min.css'
import hljs from 'highlight.js'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import sql from 'highlight.js/lib/languages/sql'
import json from 'highlight.js/lib/languages/json'
import yaml from 'highlight.js/lib/languages/yaml'
import html from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import typescript from 'highlight.js/lib/languages/typescript'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import php from 'highlight.js/lib/languages/php'
import dockerfile from 'highlight.js/lib/languages/dockerfile'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('shell', bash)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('json', json)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('html', html)
hljs.registerLanguage('xml', html)
hljs.registerLanguage('css', css)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('php', php)
hljs.registerLanguage('dockerfile', dockerfile)
```

Prefer `atom-one-dark.min.css` over `github-dark` for a Sublime-like color scheme with distinct colors for keywords, strings, functions, and comments.

**Important:** `rehype-highlight` does not auto-register languages. If you skip the explicit `hljs.registerLanguage` calls, fenced code blocks will render as a single color even though the theme CSS is loaded. Either register the languages you expect, or call `hljs.highlightElement(el)` manually on the `<code>` node.

## ChatGPT-style sizing

Use these exact classes for a ChatGPT-like hierarchy on a dark compact UI:

```jsx
function RichMessage({ content, role, animate = false }) {
  if (role !== 'user') {
    return (
      <div className="prose prose-invert max-w-none text-[var(--text)]">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight]}
          components={{
            h1: ({ children }) => <h1 className="text-[28px] font-bold text-[var(--text)] mt-8 mb-5 pb-3 border-b border-[var(--border-2)] leading-tight">{children}</h1>,
            h2: ({ children }) => <h2 className="text-[22px] font-bold text-[var(--text)] mt-7 mb-4 leading-tight">{children}</h2>,
            h3: ({ children }) => <h3 className="text-lg font-bold text-[var(--accent)] mt-6 mb-3 leading-tight">{children}</h3>,
            p: ({ children }) => <p className="mb-4 leading-[1.7] text-[15px]">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-2">{children}</ol>,
            li: ({ children }) => <li className="leading-[1.7] text-[15px]">{children}</li>,
            blockquote: ({ children }) => <blockquote className="border-l-[3px] border-[var(--accent)] pl-4 py-1 my-4 text-[var(--text-dim)] text-[15px] leading-[1.7] bg-[var(--surface-2)]/30 rounded-r-xl">{children}</blockquote>,
            code: ({ inline, className, children, ...props }) => {
              if (inline) {
                return <code className="px-1.5 py-0.5 rounded-md bg-[var(--surface-2)] text-[var(--accent)] text-[13px]" style={{ fontFamily: "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }} {...props}>{children}</code>
              }
              const match = /language-(\w+)/.exec(className || '')
              const lang = match ? match[1] : ''
              return <CodeBlock code={String(children).replace(/\n$/, '')} lang={lang} />
            },
            table: ({ children }) => <table className="w-full text-left border-collapse mb-4 text-sm">{children}</table>,
            thead: ({ children }) => <thead className="bg-[var(--surface-2)] text-[var(--text)]">{children}</thead>,
            th: ({ children }) => <th className="px-3 py-2 border border-[var(--border-2)] font-medium">{children}</th>,
            td: ({ children }) => <td className="px-3 py-2 border border-[var(--border-2)]">{children}</td>,
            a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer" className="text-[var(--accent)] hover:underline">{children}</a>,
          }}
        >
          {content || ''}
        </ReactMarkdown>
      </div>
    )
  }
  // User messages: keep plain text bubble rendering
  return <PlainTextMessage content={content} />
}
```

## User message bubble

Keep user messages as plain text inside a single subtle bubble. Match the agent text size (`text-[15px]`) so both sides read at the same scale. Compact padding to keep the bubble height low:

```jsx
<div className={cls(
  'max-w-3xl w-fit min-w-0 px-3.5 py-2 text-[15px] leading-[1.55] whitespace-pre-wrap break-words',
  m.role === 'user' ? 'bg-[var(--surface-2)] text-[var(--text)] rounded-2xl rounded-br-md' : 'text-[var(--text)]'
)}>
```

If the user says the bubble is too tall, reduce `leading` (e.g. `1.55` instead of `1.7`) before removing horizontal padding.

## Typewriter animation (word-by-word)

A ChatGPT-like typing effect is desirable, but character-by-character animation freezes the React render thread on long answers. Implement word-by-word (or token-by-token) animation instead:

```jsx
const [typingMessage, setTypingMessage] = useState(null)
const typingRef = useRef(null)

// When an assistant message arrives
const assistant = toAdd.find(m => m.role === 'assistant')
if (assistant && assistant.content != null) {
  const id = assistant.id || `typing-${assistant.timestamp}`
  const words = assistant.content.split(/(\s+)/)
  if (typingRef.current) clearInterval(typingRef.current)
  setTypingMessage({ id, full: assistant.content, words, index: 0, meta: assistant })
  typingRef.current = setInterval(() => {
    setTypingMessage(prevTyping => {
      if (!prevTyping) return null
      if (prevTyping.index >= prevTyping.words.length) {
        clearInterval(typingRef.current)
        typingRef.current = null
        return null
      }
      return { ...prevTyping, index: prevTyping.index + 1 }
    })
  }, 22)
}

// Render the partial content for the message currently being typed
const isTyping = typingMessage && (m.id === typingMessage.id || `${m.role}-${m.timestamp}-${idx}` === typingMessage.id)
const displayContent = isTyping ? typingMessage.words.slice(0, typingMessage.index).join('') : (m.content || '')
```

Adjust the interval (20–40 ms) based on how fast the user wants it to feel. Stop the interval and clear `typingMessage` once the full content is displayed.

## Copy message button

Add a small copy icon below every message. Do not show text labels — only the icon. Use a fallback for non-secure HTTP contexts because `navigator.clipboard` requires `localhost` or HTTPS:

```jsx
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const ok = () => { setCopied(true); setTimeout(() => setCopied(false), 1500) }
  const copy = () => {
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
      try { document.execCommand('copy'); ok() } catch (e) {}
      document.body.removeChild(ta)
    }
  }
  return (
    <button onClick={copy} className="text-[var(--text-dim)] hover:text-[var(--accent)] transition flex items-center" title="Копировать">
      {copied ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></svg>
      )}
    </button>
  )
}
```

Place it in the same footer row as the timestamp:

```jsx
<div className="text-[10px] text-[var(--text-dim)] mt-1 flex items-center justify-end gap-2">
  <span>{new Date(m.timestamp * 1000).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}</span>
  <CopyButton text={m.content || ''} />
</div>
```

## Code blocks

Keep the existing `CodeBlock` component but style it like a modern editor. Because `rehype-highlight` alone may leave code uncolored, manually highlight the `<code>` node with `hljs.highlightElement(el)` after mounting:

```jsx
function CodeBlock({ code, lang }) {
  const [copied, setCopied] = useState(false)
  const copy = () => { /* same fallback CopyButton logic */ }
  return (
    <div className="my-3 rounded-2xl border border-[var(--border-2)] overflow-hidden bg-[#0d0d0d]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#161616] border-b border-[var(--border-2)]">
        <span className="text-[11px] text-[var(--text-dim)] uppercase tracking-wider">{lang || 'code'}</span>
        <button onClick={copy} className="text-[11px] text-[var(--text-dim)] hover:text-[var(--accent)] transition flex items-center gap-1">
          {copied ? 'Скопировано' : 'Копировать'}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto">
        <code
          ref={(el) => {
            if (el && code) {
              el.textContent = code
              hljs.highlightElement(el)
            }
          }}
          className="text-[13px] leading-relaxed whitespace-pre"
          style={{ fontFamily: "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace" }}
        />
      </pre>
    </div>
  )
}
```

## Key rule

Do not put a border, glow, or background box around the whole assistant message. Structure comes from Markdown typography only. If the user pushes back with "не обязательно" / "that's not what I meant", strip the extra decoration and leave only the Markdown renderer.

## Build note

Vite will warn about a >500 kB JS chunk after adding `react-markdown` + highlight.js. This is acceptable for an MVP; split dynamically later if needed.
