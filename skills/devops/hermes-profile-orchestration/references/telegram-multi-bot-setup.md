# Telegram Multi-Bot Setup — Real Session Commands

Profile: `coding` cloned from `default`
Date: 2026-06-19

## Step-by-step from real setup

### 1. Create profile
```bash
hermes profile create coding --clone-from default
```
Output includes wrapper alias at `/root/.local/bin/coding`

### 2. Replace Telegram token
```bash
# Old token from default was cloned; MUST replace with new bot token
# Edit ~/.hermes/profiles/coding/.env
TELEGRAM_BOT_TOKEN=888506...:*** (new from @BotFather)
```

### 3. Start gateway
```bash
hermes -p coding gateway run
```

### 4. Verify in logs
```bash
tail -30 ~/.hermes/profiles/coding/logs/gateway.log
```
Expected:
```
[Telegram] Connected to Telegram (polling mode)
[Telegram] set_my_commands OK
```

### 5. Both bots coexist
- default bot (PID 928): existing general bot
- coding bot (PID 2495): new coding-specific bot
- Each has independent sessions, memory, skills

## Key Environment Variables

```bash
TELEGRAM_BOT_TOKEN=<unique_per_profile>
TELEGRAM_ALLOWED_USERS=<your_telegram_id>
TELEGRAM_HOME_CHANNEL=<your_telegram_id>
```

## Common Error: Token Reuse

If you forget to replace the token after `--clone-from default`, both profiles use the SAME bot. Only one gateway will receive messages. Always generate a new bot via @BotFather for each profile.
