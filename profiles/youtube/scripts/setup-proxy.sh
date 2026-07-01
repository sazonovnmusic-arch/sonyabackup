#!/bin/bash
# Setup Residential Proxy for youtube-transcript-api
# Пример настройки для разных провайдеров

# === PacketStream (рекомендую) ===
# export RESIDENTIAL_PROXY_URL="http://customer-USERNAME-cc-COUNTRY:PASSWORD@gate.packetstream.io:31112"
# Где:
#   USERNAME — твой логин на PacketStream
#   PASSWORD — API key из дашборда
#   COUNTRY — код страны: US, DE, PL, RU, UA, etc.

# === IPRoyal ===
# export RESIDENTIAL_PROXY_URL="http://user:password@proxy.iproyal.com:12321"

# === Smartproxy ===
# export RESIDENTIAL_PROXY_URL="http://user:password@gate.smartproxy.com:7000"

# Проверяем, что proxy работает
echo "Testing proxy..."
curl -x "$RESIDENTIAL_PROXY_URL" -s https://ipinfo.io/json
echo ""
echo "If you see residential IP above — proxy works!"
