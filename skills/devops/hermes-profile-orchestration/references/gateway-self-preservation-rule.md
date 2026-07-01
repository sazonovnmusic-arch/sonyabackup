# Gateway Self-Preservation Rule

## Origin
Session: Никита указал, что я не должна самостоятельно пытаться перезапускать gateway изнутри текущей сессии. Причина: gateway — это моя собственная связь с пользователем. Остановка = мгновенное отключение без возможности запустить обратно.

## The Failure Pattern
1. User says gateway is slow / not working / needs restart.
2. Agent enters reasoning loop, decides to "restart the gateway".
3. Agent runs `systemctl restart hermes-gateway` or kills the process.
4. Gateway stops → Telegram connection drops → agent's session ends.
5. Agent cannot send "done" message because it has no connection.
6. User has to manually restart service or ask another bot to do it.

## Correct Behavior
**Never self-execute gateway restart.** Three safe patterns:
1. **Give command to user** — "Run this: `systemctl restart hermes-gateway`"
2. **Delegate to another bot** — ask `@sonyacode_bot` to restart `@sonyatt_bot`'s gateway (they run as separate systemd services, no shared dependency).
3. **Use external automation** — cronjob or systemd timer that is fire-and-forget.

## Mnemonic
> "Don't operate on your own heart while it's beating."

## Memory Tag
If user says "restart gateway" or "перезапусти гейтвей" → PAUSE → route externally.
