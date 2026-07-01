# Profile Slow Response Diagnosis — Real Session Transcript

This reference captures the exact diagnosis path used on 2026-06-24 when the `instamodel` profile was "thinking too long." It can be reused verbatim for any sluggish Hermes profile.

## Symptom

Bot responds, but with large delays (10 seconds → several minutes). User says: "глянь че она так долго думает."

## Step-by-step diagnosis commands

```bash
# 1. Check which profiles exist
ls -la ~/.hermes/profiles/

# 2. Check systemd services (reveals which are running / failed)
systemctl list-units --type=service | grep -i hermes

# 3. Inspect recent logs for the sluggish profile
journalctl -u hermes-gateway-<profile>.service --since "2 hours ago" -n 200 --no-pager

# 4. Check running processes (multiple PIDs = multiple gateways fighting?)
ps aux | grep -i hermes | grep -v grep
```

## Common root causes found in this session

### 1. Telegram Flood Control (most common)

**Log pattern:**
```
WARNING gateway.platforms.telegram: [Telegram] Telegram flood control, waiting 277.0s
WARNING gateway.platforms.telegram: [Telegram] Telegram flood control, waiting 148.0s
WARNING gateway.platforms.telegram: [Telegram] Flood control exceeded. Retry in 93 seconds
```

**Why it happens:** Bot sends too many messages too fast (chunked long responses, inline edits, retry loops). Telegram rate-limits the bot.

**Immediate fix:** `systemctl restart hermes-gateway-<profile>.service` — resets the rate-limit window.

**Long-term fix:**
- Avoid rapid-fire edits to the same message (MarkdownV2 edit → plain text fallback churn)
- Reduce `message_timestamps` frequency or add delays in config
- If persistent, consider webhook mode instead of polling

### 2. Tool execution errors (infinite retry / stall)

**Log pattern:**
```
WARNING agent.tool_executor: Tool memory returned error (0.00s): {"error": "Unknown action 'None'"}
WARNING agent.tool_executor: Tool skill_manage returned error (0.10s): {"success": false, "error": "Could not find a match for old_string"}
WARNING agent.tool_executor: Tool execute_code returned error (0.16s): {"status": "error", "output": "ImageFont.truetype..."}
WARNING agent.tool_executor: Tool terminal returned error (150.92s): {"output": "", "exit_code": -1, "error": "BLOCKED: Command denied by user"}
WARNING agent.tool_executor: Tool write_file returned error (0.00s): {"error": "Background review denied non-whitelisted tool"}
```

**Why it happens:** Agent enters a loop trying to fix memory/skills/files, but each attempt fails. Each failure triggers a new LLM turn. The loop burns time and floods Telegram with retry messages.

**Fix:**
- Restart the gateway (breaks the loop)
- Check if the skill/memory file actually exists before patching
- If `write_file` is denied by Background Review, do NOT retry — only memory/skill tools are allowed in background mode

### 3. Heavy model on shared infrastructure

**Check:**
```bash
# In config.yaml — what model is configured?
grep "model.default" ~/.hermes/profiles/<profile>/config.yaml
```

MoE models (>200B params) on shared inference can add 10-30s per token generation.

**Fix:**
```bash
hermes config set model.default <lighter-model> --profile <profile>
systemctl restart hermes-gateway-<profile>.service
```

### 4. Context bloat (huge session DB)

```bash
du -sh ~/.hermes/profiles/<profile>/
ls -la ~/.hermes/profiles/<profile>/sessions/
```

If sessions directory is >100MB, the agent is dragging enormous context.

**Fix:** Archive old sessions or lower `max_turns` in config.

## Quick decision table

| Log shows | Likely cause | Fix |
|---|---|---|
| `flood control, waiting Xs` | Telegram rate limit | Restart gateway |
| Tool errors repeating rapidly | Tool failure loop | Restart gateway + fix broken skill |
| `Connection error` / API timeout | Provider down | Swap provider or model |
| High CPU in `ps aux`, low RAM | Context bloat or stuck loop | Restart + prune sessions |
| No errors, just slow | Heavy model / shared infra | Switch to lighter model |

## Verification after restart

```bash
systemctl status hermes-gateway-<profile>.service --no-pager
journalctl -u hermes-gateway-<profile>.service -n 20 --no-pager
```

Look for `Active: active (running)` and clean startup logs.
