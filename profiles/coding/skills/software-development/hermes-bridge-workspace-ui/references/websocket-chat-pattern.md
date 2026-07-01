---
title: WebSocket-first chat delivery for Hermes Bridge UI
scope: hermes-bridge-workspace-ui
---

# WebSocket-чат в Hermes Bridge UI

## Зачем

Polling — даже быстрый (500 мс) — всё ещё создаёт задержку и лишнюю нагрузку. WebSocket позволяет серверу **pushить** новые сообщения в UI мгновенно, как только Hermes их записал в `state.db`. Это даёт Telegram-like опыт: сообщение появляется сразу, целиком, без необходимости обновлять страницу.

## Когда использовать

- Пользователь жалуется, что ответы приходят "через раз" или требуют обновления страницы.
- Polling уже настроен правильно, но всё равно ощущается дергано.
- Нужна максимально плавная доставка assistant-ответов.

## Архитектура

```
Browser  ◀──WebSocket──▶  FastAPI Bridge  ◀──sqlite/CLI──▶  Hermes  ──▶  state.db
                              │
                              └── при появлении нового assistant-сообщения
                                  рассылает его подписанным клиентам
```

## Backend: FastAPI WebSocket

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio, json

app = FastAPI()

# profile -> session_id -> set of websockets
_subscribers: dict[str, dict[str, set[WebSocket]]] = {}

async def subscribe(profile: str, session_id: str, ws: WebSocket):
    await ws.accept()
    _subscribers.setdefault(profile, {}).setdefault(session_id, set()).add(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive, ignore client messages
    except WebSocketDisconnect:
        pass
    finally:
        _subscribers.get(profile, {}).get(session_id, set()).discard(ws)

@app.websocket("/ws/sessions/{profile}/{session_id}")
async def session_ws(websocket: WebSocket, profile: str, session_id: str):
    await subscribe(profile, session_id, websocket)

async def broadcast(profile: str, session_id: str, message: dict):
    clients = _subscribers.get(profile, {}).get(session_id, set())
    dead = []
    for ws in clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)
```

## Откуда вызывать broadcast

После того как Hermes CLI завершился, прочитай новые сообщения из `state.db` и разошли их:

```python
# После hermes chat -q ... --resume
new_messages = fetch_new_assistant_messages(profile, session_id, after_id)
for msg in new_messages:
    await asyncio.gather(
        broadcast(profile, session_id, {
            "type": "message",
            "message": {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content or "",
                "timestamp": msg.timestamp,
                "active": msg.active,
            }
        }),
        return_exceptions=True,
    )
```

Если вызывается из синхронного контекста (например, после `subprocess.run`), используй:

```python
asyncio.run(broadcast(...))
```

или сохраняй задачу в очередь для event loop.

## Frontend: React WebSocket hook

```ts
function useSessionSocket(profile: string | null, sessionId: string | null, onMessage: (msg: any) => void) {
  useEffect(() => {
    if (!profile || !sessionId) return

    const ws = new WebSocket(`ws://${window.location.host.replace(':3000', ':8123')}/ws/sessions/${profile}/${sessionId}`)

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'message') onMessage(data.message)
    }

    ws.onerror = (e) => console.error('ws error', e)

    return () => ws.close()
  }, [profile, sessionId])
}
```

Использование:

```ts
useSessionSocket(selected?.name, activeSessionId, (msg) => {
  setMessages(prev => {
    if (prev.some(m => m.id === msg.id)) return prev
    return [...prev, msg]
  })
})
```

## Фолбэк на polling

WebSocket может не работать через некоторые прокси/сети. Держи polling как fallback:

```ts
const [wsReady, setWsReady] = useState(false)

useEffect(() => {
  if (!profile || !sessionId) return
  const ws = new WebSocket(...)
  ws.onopen = () => setWsReady(true)
  ws.onclose = () => setWsReady(false)
  return () => ws.close()
}, [profile, sessionId])

// polling только если WebSocket не подключён
useEffect(() => {
  if (!profile || !sessionId || wsReady) return
  const interval = setInterval(() => pollMessages(), 500)
  return () => clearInterval(interval)
}, [profile, sessionId, wsReady])
```

## Практические замечания

- **Автоскролл** должен быть `behavior: 'auto'`, не `'smooth'`, иначе сообщение будет "убегать" от пользователя.
- **Typewriter-анимацию не использовать** — она конфликтует со скроллом и восприятием. Показывай сообщение целиком сразу.
- **user-сообщение** добавляй локально в UI сразу после отправки, не жди WebSocket — так интерфейс отзывчивый.
- **Фильтр дублей** по `id` обязателен: WebSocket и polling могут прислать одно и то же сообщение.
- **Reconnect**: если соединение падает, переподключайся с экспоненциальным бэкоффом (1с, 2с, 4с … 30с).

## Проверка

1. Отправить сообщение — user-сообщение появляется мгновенно.
2. Через несколько секунд assistant-ответ появляется целиком, без обновления страницы.
3. Переключиться в другую вкладку/вернуться — соединение восстанавливается, сообщения не теряются.
4. Медленный/прерывистый интернет — UI переключается на polling и продолжает работать.

## Связанные паттерны

- `references/chat-polling-patterns.md` — фолбэк polling, если WebSocket недоступен.
- `references/chat-ui-performance-patterns.md` — пагинация, collapsing, layout.
