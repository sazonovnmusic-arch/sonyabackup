---
name: hermes-remote-access
description: Подключение Hermes Desktop App (Hermes One) к удалённым серверам и профилям через HTTP API (api_server) или Tailscale/VPN. Траблшутинг соединений 401 и проверка gateway-конфигурации.
category: devops
---

# Hermes Remote Access

## Когда применять
- Пользователь пытается подключить Hermes One / Desktop App к удалённому серверу
- Вопросы про «Connect via SSH» или «Connect to Remote Hermes»
- Не работает соединение с api_server (порт 8642 и т.д.)
- Desktop показывает ошибку «OpenRouter API key missing», но на самом деле проблема в другом
- Нужно управлять удалёнными профилями через Desktop App

## Ключевые факты

### Важно: gateway vs api_server — разные вещи!
**Gateway** (Telegram, Discord и т.д.) — исходящие соединения, **не слушает порты**.

**api_server** — HTTP API, которое Hermes One/Desktop App использует для подключения к удалённому профилю.

Если `api_server` не настроен — Desktop подключиться **не сможет**.

### Режимы работы gateway
- По умолчанию `api_server` **отключён** в `platforms`.
- Если `api_server` не включён — **нет LISTEN-порта**.

### Для подключения Desktop App нужен api_server
1. На сервере `api_server` должен быть включён и слушать порт
2. Указан `api_key` (если требуется auth)
3. Порт доступен с машины Desktop App (через Tailscale/VPN или публичный IP + reverse proxy)

### Hermes One (Desktop App) vs api_server
- Hermes One на Mac/Windows **не подключается** к профилю напрямую
- Он подключается к **api_server endpoint** сервера
- Фактический профиль (default/coding/youtube/traffic) выбирается на сервере — Desktop этого не знает

## Настройка api_server (на сервере)

### 1. Включить api_server в конфиге
```yaml
platforms:
  api_server:
    enabled: true
    extra:
      port: 8642
      api_key: "твой-секретный-ключ"
```

Ключ **обязателен** для remote-подключения (безопасность).

### 2. Перезапустить gateway
```bash
sudo hermes gateway restart --system
# или
systemctl restart hermes-gateway.service
```

### 3. Проверить, что слушает
```bash
ss -tlnp | grep 8642
```
Если пусто — смотри логи `journalctl -u hermes-gateway`.

## Подключение Desktop App

### Вариант A: Tailscale/VPN (рекомендуется для VPS/Beget)
Наиболее простой и безопасный способ. Tailscale создаёт mesh-VPN — сервер и Mac видят друг друга по приватным IP.

На сервере:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

На Mac:
- Установить Tailscale.app → войти в ту же сеть
- Hermes Desktop → Settings → Gateway URL: `http://<tailscale-ip-сервера>:8642`
- API Key: тот же ключ, что в `api_server.extra.api_key`

### Вариант B: Reverse proxy + HTTPS (для публичного доступа)
Нужен домен + nginx/Caddy:
```
server {
    listen 443 ssl;
    server_name hermes.yourdomain.com;
    location / {
        proxy_pass http://localhost:8642;
        proxy_set_header Host $host;
    }
}
```
Desktop → `https://hermes.yourdomain.com`

### Вариант C: SSH-туннель (для теста)
```bash
ssh -L 8642:localhost:8642 user@remote_host -N
```
Desktop → `http://localhost:8642`

## Питфоллы

1. **Desktop показывает «OpenRouter API key missing», но ключ стоит**
   - Это **UX баг #39365**: Desktop путает gateway-auth 401 с provider-auth 401.
   - Реальная проблема: неверный `API_SERVER_KEY` или api_server не принимает подключение.
   - Проверь: `curl -H "Authorization: Bearer <ключ>" http://<ip>:8642/v1/models`

2. **Порт не доступен снаружи**
   - Beget/VPS: firewall/iptables блокирует порт. Открыть: `ufw allow 8642/tcp`.
   - Shared-хостинг: api_server не запустится вообще, нужен VDS/VPS.

3. **api_server не запущен**
   - Проверить `systemctl status hermes-gateway`
   - Проверить `hermes gateway status` — выведет все платформы

4. **Desktop не видит 4 профиля**
   - Desktop подключается к **api_server endpoint** — это один профиль (default).
   - Чтобы писать в другие профили — нужно 4 api_server на разных портах (каждый профиль свой systemd gateway) или использовать Telegram.
   - **Hermes One не умеет переключать профили** — один endpoint = один профиль.

5. **Beget shared hosting**
   - Hermes gateway вряд ли запустится. Нужен VDS/VPS с systemd.

## Ссылки
- `references/desktop-connect-tailscale.md` — пошаговая инструкция для Tailscale + Desktop
- `references/desktop-error-39365.md` — баг #39365: «OpenRouter key missing» = gateway 401