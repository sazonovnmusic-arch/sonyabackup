#!/bin/bash
# Простой запуск YouTube gateway — один раз
LOCK=/tmp/youtube-gateway.lock
LOG=/root/.hermes/profiles/youtube/logs/gateway-current.log

# Загружаем .env
set -a
source /root/.hermes/profiles/youtube/.env
set +a

# Если уже запущен — выходим
pgrep -f "hermes -p youtube gateway" > /dev/null && exit 0

# Запускаем
cd /root
exec hermes -p youtube gateway run > "$LOG" 2>&1
