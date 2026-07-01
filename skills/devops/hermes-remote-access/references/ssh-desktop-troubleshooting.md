# SSH Desktop Troubleshooting Reference

## Быстрая диагностика

### Проверить, что gateway слушает HTTP
```bash
ss -tlnp | grep hermes
lsof -Pan -p $(pgrep -f "hermes_cli.main gateway" | head -1) -i | grep LISTEN
```
Если пусто — HTTP API не работает. Сначала включай `use_gateway`.

### Проверить конфиг gateway
```bash
grep -n "use_gateway\|gateway:" ~/.hermes/config.yaml
```

### Статус сервисов
```bash
systemctl list-units --type=service | grep hermes
systemctl status hermes-gateway
```

## Типичные ошибки Desktop App

### "Could not connect via SSH or reach Hermes on the remote"
Причины:
1. `use_gateway: false` — gateway не слушает HTTP
2. SSH ключ не подходит (проверить `ssh user@host` без пароля)
3. Hermes gateway не запущен вообще (`systemctl status hermes-gateway`)

### "Could not reach Hermes at this URL"
Причины:
1. Порт не открыт или не слушает
2. API key неверный (если включена аутентификация)
3. URL неверный

## Включение HTTP gateway
```bash
hermes config set agent.use_gateway true
hermes config set gateway.port 8642
systemctl restart hermes-gateway
# Проверить
ss -tlnp | grep 8642
```

## SSH-туннель (если gateway уже слушает)
```bash
ssh -L 8642:localhost:8642 user@remote_host -N
# Затем в Desktop App: http://localhost:8642
```