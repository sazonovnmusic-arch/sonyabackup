#!/bin/bash
# Hermes YouTube Gateway Watchdog — стабильный перезапуск
LOG=~/.hermes/profiles/youtube/logs/watchdog.log
ENV_FILE=~/.hermes/profiles/youtube/.env

# Загружаем .env переменные
set -a
source "$ENV_FILE" 2>/dev/null || true
set +a

while true; do
    if ! pgrep -f "hermes -p youtube gateway" > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S'): YouTube gateway DOWN — restarting..." >> "$LOG"
        # Запускаем в абсолютно новой сессии (не привязан к терминалу)
        nohup bash -c "source $ENV_FILE && cd /root && hermes -p youtube gateway run > ~/.hermes/profiles/youtube/logs/gateway.log 2>&1" > /dev/null 2>&1 &
        sleep 10
    fi
    sleep 30
done
