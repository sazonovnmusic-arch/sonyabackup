---
title: Reliable chat polling for Hermes Bridge UI
scope: hermes-bridge-workspace-ui
---

# Надёжный polling чата в Hermes Bridge UI

## Проблема

Bridge запускает `hermes chat -q ... --resume` в фоновом потоке и сразу возвращает `task_id`. UI должен опрашивать state.db, пока не появится assistant-ответ. Стандартная реализация «верни последнее assistant-сообщение» ломается, когда:

- Hermes пишет несколько сообщений подряд (пустой assistant → tool → tool → финальный assistant);
- polling редкий (2 сек) — ответ появляется, но UI узнаёт с опозданием;
- typewriter-анимация последнего сообщения вызывает сотни ререндеров и конфликтует со скроллом;
- smooth auto-scroll не поспевает за ростом сообщения.

В итоге ответ либо не отображается, либо требует обновления страницы.

## Решение

### 1. Backend poll возвращает массив новых сообщений

```python
@app.get("/api/sessions/{profile}/{session_id}/poll")
def poll_message(profile: str, session_id: str, after_id: int | None = None):
    with db(profile) as conn:
        sql = """
            SELECT id, role, content, timestamp, active
            FROM messages
            WHERE session_id = ? AND role = 'assistant' AND active = 1
        """
        params = [session_id]
        if after_id is not None:
            sql += " AND id > ?"
            params.append(after_id)
        sql += " ORDER BY timestamp ASC"
        rows = conn.execute(sql, params).fetchall()
        if rows:
            return [Message(..., content=r["content"] or "", ...) for r in rows]

    active_tasks = [t for t in running_tasks.values()
                    if t["profile"] == profile and t["session_id"] == session_id and not t["done"]]
    return {"status": "processing", "session_id": session_id, "active_tasks": len(active_tasks)}
```

Важно:
- Возвращать **только assistant** — иначе user-сообщения дублируются, потому что UI уже добавил свой user локально.
- Возвращать **массив** всех новых сообщений, а не последнее.
- Отдавать `active_tasks`, чтобы UI знал, когда остановить polling.

### 2. UI запоминает max id перед отправкой

```js
let afterId = 0
const latestRes = await fetch(`${API}/sessions/${profile}/${sessionId}?limit=1&offset=0&order=desc`)
const latest = await latestRes.json()
if (Array.isArray(latest) && latest.length > 0) {
  afterId = Math.max(...latest.map(m => m.id || 0), 0)
}
```

Для новой сессии `afterId` останется 0 — это нормально, poll просто вернёт все assistant-сообщения.

### 3. Polling каждые 500 мс с защитой от дублей

```js
const seenIds = new Set()
const pollInterval = setInterval(async () => {
  const pollRes = await fetch(`${API}/sessions/${profile}/${sessionId}/poll?after_id=${afterId}`)
  const data = await pollRes.json()

  if (Array.isArray(data) && data.length > 0) {
    const newMessages = data
      .filter(m => m && m.timestamp != null && m.content != null)
      .filter(m => !seenIds.has(m.id))

    if (newMessages.length > 0) {
      newMessages.forEach(m => seenIds.add(m.id))
      afterId = Math.max(afterId, ...newMessages.map(m => m.id || 0))
      setMessages(prev => {
        const existingIds = new Set(prev.map(m => m.id))
        const toAdd = newMessages.filter(m => !existingIds.has(m.id))
        return [...prev, ...toAdd]
      })
    }
  } else if (data.active_tasks === 0) {
    clearInterval(pollInterval)
    setLoading(false)
  }
}, 500)
```

### 4. Убрать typewriter-анимацию

Анимация «печатания» символа за символом конфликтует с автоскроллом и делает чат дерганным. Ответ должен появляться целиком сразу, как в Telegram.

### 5. Автоскролл без анимации

```js
useEffect(() => {
  if (bottomRef.current) {
    bottomRef.current.scrollIntoView({ behavior: 'auto' })
  }
}, [messages.length, loading])
```

### 6. Фильтровать пустые assistant-сообщения

Hermes иногда пишет assistant-строку с пустым `content` перед tool-вызовами. В UI их можно не показывать или показывать, но не ожидать от них контента. В polling-фильтре `m.content != null` обязателен.

## Проверка

1. Отправить сообщение в новую сессию — user-сообщение появляется мгновенно.
2. Через 3–10 секунд появляется assistant-ответ целиком.
3. Обновлять страницу не требуется.
4. Ответ не дублируется.
5. Скролл остаётся внизу.

## Связанные антипаттерны

- `const API = '/api'` в production-сборке, раздаваемой `npx serve`, работать не будет. Используй `http://<bridge-host>:8123/api` или reverse proxy.
- `<div>>_</div>` в JSX ломает парсер — пиши `&gt;_`.
- Авто-загрузка первой сессии при выборе агента с большим числом сообщений может повесить UI. Загружай историю только по клику или по сохранённому `activeSessionId`.
