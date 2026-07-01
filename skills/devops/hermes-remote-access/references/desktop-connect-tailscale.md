# Подключение Hermes Desktop App через Tailscale

> Прагматичный способ соединить Mac и удалённый VPS (Beget и др.) без public IP, reverse proxy и SSL-сертификатов.

## Зачем Tailscale
- VPS (Beget) и Mac видят друг друга по приватным IP (100.x.x.x) как в одной локалке.
- Не нужен public IP, домен, reverse proxy, SSL.
- Трафик шифруется WireGuard-протоколом.

## Шаг 1: Установить Tailscale на сервер
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

Скопируй ссылку для авторизации, открой в браузере.

Запомни Tailscale IP сервера:
```bash
tailscale ip -4
# 100.x.y.z
```

## Шаг 2: api_server на сервере
```bash
# Проверить/установить ключ
hermes config set platforms.api_server.enabled true
hermes config set platforms.api_server.extra.port 8642
hermes config set platforms.api_server.extra.api_key "твой-секретный-ключ"

# Перезапустить gateway
sudo hermes gateway restart --system
```

Проверить:
```bash
ss -tlnp | grep 8642
curl -H "Authorization: Bearer твой-с...юч" http://localhost:8642/api/openai/v1/models
```

## Шаг 3: Tailscale на Mac
1. Скачать [Tailscale для macOS](https://tailscale.com/download/mac)
2. Войти в ту же Tailzone (нужен тот же Google/GitHub аккаунт)
3. Проверить ping: `ping 100.x.y.z` (Tailscale IP сервера)

## Шаг 4: Hermes Desktop на Mac
- **Settings → Connection → Gateway URL**: `http://100.x.y.z:8642`
- **API Key**: тот же ключ, что на сервере в `api_server.extra.api_key`
- Профиль выбирается на сервере (default = @sonyabot). Чтобы переключить — меняй active профиль на сервере.

## Траблшутинг
| Симптом | Причина | Фикс |
|---------|---------|------|
| «Could not reach Hermes» | Порт закрыт firewall | `ufw allow 8642/tcp` |
| «OpenRouter API key missing» | Баг #39365 — на самом деле неверный API_SERVER_KEY | Проверить совпадение ключа |
| Desktop видит, но не отвечает | api_server включён, но профиль не default | `hermes profile show` |

## Альтернативы
- **SSH-туннель**: `ssh -L 8642:localhost:8642 user@100.x.y.z -N` → Desktop → `http://localhost:8642`
- **Reverse proxy (nginx)**: если нужен публичный доступ, см. SKILL.md основной