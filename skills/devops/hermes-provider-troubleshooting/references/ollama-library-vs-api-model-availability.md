# Ollama Cloud: Library vs API Model Availability

Date: 2026-06-30
Profile: coding

## Problem

Модель `ornith` доступна на сайте: `https://ollama.com/library/ornith`
Но при попытке использовать через Ollama Cloud API (`https://ollama.com/v1`) — возвращает 404.

## Evidence

### 1. Модель есть на сайте
```bash
curl -sI https://ollama.com/library/ornith | head -1
# HTTP/2 200
```

### 2. Нет в списке API
```bash
curl -s https://ollama.com/v1/models | grep ornith
# (пусто)
```

### 3. Inference call 404
```bash
curl -s -X POST https://ollama.com/v1/chat/completions \
  -H "Authorization: Bearer ..." \
  -H "Content-Type: application/json" \
  -d '{"model": "ornith", "messages": [{"role": "user", "content": "hi"}]}'
# {"error":{"message":"model \"ornith\" not found"}}
```

### 4. Логи Hermes
```
agent.conversation_loop: API call failed after 3 retries.
HTTP 404: model "ornith" not found
provider=ollama-cloud model=ornith
```

## Fix

Сменить на модель, которая реально есть в API:
```bash
hermes config set model.default kimi-k2.7-code --profile coding
```

Проверенные доступные модели на момент сессии:
- `kimi-k2.6`
- `kimi-k2.7-code`
- `deepseek-v3.1:671b`
- `mistral-large-3:675b`
- `gemini-3-flash-preview`
- `devstral-2:123b`

## Lesson

`ollama.com/library/<name>` != `ollama.com/v1/models`. Не все модели из публичной библиотеки доступны через Cloud API. Всегда проверять через `/v1/models` перед установкой в конфиг.
