# React UI blank page after patching

A blank `#root` after `npm run build` and `serve` usually means the React bundle crashes during initial mount. `curl` returns correct `index.html` and the static assets load with HTTP 200, but nothing renders because a state/callback/component is missing or broken.

## Most common causes in this workspace

### 1. A `useState` declaration was accidentally removed while reordering hooks

When patching a long component, moving or adding hooks can delete an existing `useState` line. The minified bundle still builds, but React throws at mount because `setMessages` (or similar) is referenced without a state declaration.

**Quick check before building:**
```bash
cd ~/ai-workspace/ui
grep -n "const \[messages" src/App.jsx
# If nothing is returned, the state was lost during a patch.
```

**Fix:** restore the declaration exactly where the other `useState` hooks live, before any `useRef`/`useCallback`/`useEffect`:
```jsx
const [sessions, setSessions] = useState([])
const [historyOpen, setHistoryOpen] = useState(false)
const [messages, setMessages] = useState([])   // must exist
```

### 2. JSX contains an unescaped `>` or `<`

Text like `<div>>_</div>` or `<>_</>` breaks JSX parsing. Use `&gt;_` or wrap the character in an expression: `{ '>' }`.

### 3. Line-number corruption from `read_file` output

Hermes `read_file` returns lines prefixed with `1|`, `2|`, etc. If that output is written back into a JSX/JS file, Vite may still build it (because the prefix is valid syntax in some places), but runtime errors or blank pages occur. Run `scripts/fix-line-number-corruption.py` or rewrite the file cleanly with `write_file`/`execute_code`.

### 4. Unstable `useEffect` dependencies causing an exception before first paint

A `useEffect` that creates an `EventSource` or `WebSocket` can throw if its dependency array includes callbacks that are not memoized, or if the URL is malformed. This kills the initial render and leaves `#root` empty.

**Safer pattern for live SSE connection:**
```jsx
const liveRef = useRef(null)

useEffect(() => {
  if (!activeSessionId || !selected) return
  const url = `${EVENTS_URL}/${selected.name}/${activeSessionId}/events`
  if (liveRef.current?.url === url) return   // already connected to same session

  liveRef.current?.close()
  const es = new EventSource(url)
  liveRef.current = es
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'message') addMessages(data)
    } catch {}
  }
  es.onerror = () => {
    // auto-reconnect is built into EventSource; no manual setTimeout needed
  }
  return () => es.close()
}, [activeSessionId?.id, selected?.name])   // stable primitives, not callbacks
```

Avoid putting `addMessages`, `openLive`, or `closeLive` callbacks directly in the dependency array unless they are wrapped in `useCallback` with stable deps.

### 5. EventSource URL blocked in browser automation

If `new EventSource(...)` throws synchronously in the test environment (some proxies block it), the whole app can fail to mount. Defensive wrapper:
```jsx
try {
  liveRef.current = new EventSource(url)
} catch (e) {
  console.warn('SSE blocked, falling back to polling', e)
  liveRef.current = null
}
```

## Diagnostic checklist

1. `curl http://<host>:3000` returns HTML and assets return 200.
2. Open browser console and look for the **first** thrown error, not the last.
3. Search the built asset for the missing component/state name:
   ```bash
   grep -o "contains ChatView" <(node -e "const fs=require('fs');const j=fs.readFileSync('dist/assets/*.js','utf8');console.log('ChatView', j.includes('ChatView'), 'messages state', /const \[messages, setMessages\]/.test(j))")
   ```
4. If the bundle is missing a component/state, the source file lost it during patching — regenerate or restore from backup.
5. If the bundle is complete but the page is blank, check the console for a synchronous throw in `useEffect` or `EventSource`.

## Prevention

- Keep the custom UI and Bridge backups before large experiments:
  ```bash
  cp -r ~/ai-workspace/ui ~/ai-workspace/ui_backup_$(date +%Y%m%d_%H%M%S)
  cp -r ~/ai-workspace/bridge ~/ai-workspace/bridge_backup_$(date +%Y%m%d_%H%M%S)
  ```
- After patching hooks in a large component, grep for every setter (`setMessages`, `setLoading`, etc.) and confirm its corresponding `useState` exists.
- Prefer `write_file`/`execute_code` for replacing a whole block; use `patch` only for small, targeted changes.

## See also

- `references/realtime-chat-delivery.md` — SSE/WebSocket push implementation.
- `references/chat-polling-patterns.md` — reliable polling fallback.
- `scripts/verify-ui-render.sh` — quick probe to check if `#root` is empty.
