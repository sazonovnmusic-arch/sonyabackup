#!/bin/bash
LOG=~/.hermes/profiles/coding/watchdog.log
while true; do
    if ! pgrep -f "hermes -p coding gateway" > /dev/null; then
        echo "$(date): Coding gateway down, restarting..." >> "$LOG"
        nohup /usr/local/lib/hermes-agent/venv/bin/hermes -p coding gateway run > /dev/null 2>> ~/.hermes/profiles/coding/gateway.log &
        sleep 10
    fi
    sleep 60
done
