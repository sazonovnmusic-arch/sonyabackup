# Баг #39365: Desktop показывает «OpenRouter API key missing» при 401 gateway auth

## Суть
Hermes Desktop App (macOS/Windows) при неудачном подключении к api_server может показывать **обманчивую ошибку**:

> «OpenRouter API key missing»

Но OpenRouter ключ **на месте** и рабочий.

**Реальная проблема** — gateway auth 401: неверный или отсутствующий `API_SERVER_KEY` (ключ api_server), или api_server не принимает подключение вообще.

Это **UX баг** Hermes Desktop: он не различает `401 от api_server` (gateway auth) и `401 от LLM-провайдера` (OpenRouter).

## Быстрая диагностика

Шаг 1: Проверить api_server напрямую с сервера
```bash
curl -H "Authorization: Bearer <ВАШ_API_SERVER_KEY>" \
     http://localhost:8642/v1/models
```
- HTTP 200 + JSON моделей → api_server работает, ключ верен
- HTTP 401 → ключ неверный или не задан
- Connection refused → api_server не слушает (проверить `ss -tlnp | grep 8642`)

Шаг 2: Проверить с Mac/Desktop хоста
```bash
curl -H "Authorization: Bearer <ВАШ_API_SERVER_KEY>" \
     http://<IP_СЕРВЕРА>:8642/v1/models
```
- HTTP 200 → порт открыт, всё ок
- Timeout → firewall блокирует порт
- HTTP 401 → ключ неверный

## Если Desktop показывает «OpenRouter API key missing»
1. **Не трогай OpenRouter ключ** — он не при чём
2. Проверь `API_SERVER_KEY` в Desktop Settings
3. Убедись, что он совпадает с `platforms.api_server.extra.api_key` на сервере
4. Если ключ пустой — задай его: `hermes config set platforms.api_server.extra.api_key "..."`

## Примечание
Этот баг существовал на версиях Desktop до ~v0.17. Возможно, уже пофикшен в новых версиях. Но если вы встретили — теперь знаете причину.

## References
- Issue GitHub: https://github.com/NousResearch/hermes-agent/issues/39365