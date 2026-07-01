# Gateway Token Collision

## Symptom

When launching `hermes -p <profile> gateway run`, the startup fails with:

```
ERROR gateway.platforms.base: [Telegram] Telegram bot token already in use (PID xxx).
Stop the other gateway first.
```

## Root Cause

Each Telegram bot token can only maintain one active polling/webhook session. If another Hermes profile is already using the same TELEGRAM_BOT_TOKEN, Telegram rejects the second connection.

## Fix

### Option 1: Unique token per profile (recommended)

Generate a separate bot in @BotFather for each profile and set unique TELEGRAM_BOT_TOKEN in each profile's .env.

### Option 2: Stop the old gateway first

```bash
hermes -p <old_profile> gateway stop
hermes -p <new_profile> gateway run
```

## Prevention

List all active tokens:
```bash
grep -r "TELEGRAM_BOT_TOKEN" ~/.hermes/profiles/*/.env | grep -v "^#"
```

Ensure each token is unique across profiles.