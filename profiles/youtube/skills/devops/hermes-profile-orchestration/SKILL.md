---
name: hermes-profile-orchestration
description: "Isolate Hermes workloads into dedicated profiles with separate memory, skills, and messaging bots. Covers multi-profile creation, Telegram multi-bot setup, and workspace isolation patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, profiles, multi-agent, telegram, gateway, isolation, coding-agent]
    related_skills: [hermes-agent, server-management]
---

# Hermes Profile Orchestration

This skill governs creating and managing **isolated Hermes profiles** for different use-cases (coding, research, personal, etc.), each with its own memory, skills, sessions, and dedicated Telegram bot.

## When to Use This Skill

- User wants a **dedicated coding agent** separate from general chat
- User asks about "separate bot for X", "another profile", "isolated memory"
- User wants **multiple Telegram bots** for different tasks
- User wants to **avoid polluting main memory** with task-specific context
- Setting up long-running autonomous agents with isolated identity

## Core Concepts

| Concept | What It Means |
|---------|---------------|
| **Profile** | Isolated `~/.hermes/profiles/<name>/` directory with own config, .env, memory, skills, sessions |
| **Memory Isolation** | Each profile has separate SQLite DB, user profile, and cross-session memory |
| **Skill Isolation** | Skills can be loaded per-profile; agent-created skills go to the active profile |
| **Gateway Isolation** | Each profile can run its own Telegram/Discord/etc bot |
| **Model Sharing** | All profiles can use the same LLM provider without conflict |

## Workflow: Create Dedicated Coding Agent

### 1. Create Profile (clone from default)

```bash
# Clone existing profile (copies config, .env, skills)
hermes profile create coding --clone-from default

# Verify
hermes profile list
hermes profile show coding
```

**What gets cloned:** `config.yaml`, `.env`, `SOUL.md`, `skills/`
**What is fresh:** sessions, state.db, memory

### 2. Configure Separate Telegram Bot

Obtain a new bot token from @BotFather, then update the profile `.env`:

```bash
# Edit the profile .env
nano ~/.hermes/profiles/coding/.env

# Set NEW bot token (do NOT reuse the default bot token)
TELEGRAM_BOT_TOKEN=888506...:AAGpZOie9j7UMQ7RDHMVUxDiLG53RhiOFqk
TELEGRAM_ALLOWED_USERS=<your_user_id>
TELEGRAM_HOME_CHANNEL=<your_user_id>
```

**Critical:** Two profiles using the same `TELEGRAM_BOT_TOKEN` will collide. Each profile needs its own bot.

### 3. Launch Gateway for New Profile

```bash
# Check if already running
hermes -p coding gateway status

# Start foreground (for testing)
hermes -p coding gateway run

# Or start as background process
hermes -p coding gateway start
```

### 4. Verify Both Bots Work

| Bot | Profile | Purpose |
|-----|---------|---------|
| `@original_bot` | `default` | General tasks, chat, setup |
| `@coding_bot` | `coding` | Code, files, dev work |

Send `/start` to the new bot. It should respond with no memory of previous conversations (clean slate).

## Multi-Bot Pitfalls

### Flood Control (Telegram Rate Limiting)

**Symptom:** Bot responds intermittently, log shows:
```
Overflow continuation send failed: Flood control exceeded. Retry in 61 seconds
```

**Cause:** Multiple bots from same IP sending messages rapidly; or one bot sending chunked long responses too fast.

**Fix:**
- Wait 60 seconds — rate limit resets automatically
- Avoid rapid-fire messages to multiple bots simultaneously
- For persistent issues, reduce `message_timestamps` or add delays in config
- Consider webhook mode instead of polling for high-traffic bots

### Alias Not in PATH

After `profile create`, Hermes warns:
```
/root/.local/bin is not in your PATH
```

**Fix:**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
# Now you can use:
coding chat
coding gateway status
```

### Gateway Conflicts (Same Port)

If both profiles try to bind API Server or webhook to the same port, the second will fail. Ensure unique ports in each profile's `config.yaml`.

## Lazy Skill Loading Strategy

When working with a dedicated profile, prefer **on-demand skill loading** rather than preloading all skills:

```
# In session, user asks for code review:
/skill github-code-review
# Agent loads it, performs review, skill stays available for session
```

This keeps system prompt lean and token usage low. Document this approach when user explicitly requests it.

## Communication Preferences (User-Specific)

When this skill is loaded for a user who previously worked with the agent, check memory for:
- Voice/TTS preference (some users reject voice after trying it)
- Terminal vs messenger preference
- Preferred model for coding profile

Do NOT assume terminal is preferred — ask or check memory.

## Reference Files

- `references/telegram-multi-bot-setup.md` — Exact commands and .env structure from real session
- `references/flood-control-troubleshooting.md` — Telegram flood control patterns and fixes

## Default Profile .env Location (CRITICAL)

The `hermes-gateway.service` (default profile) runs with `HERMES_HOME=/root/.hermes`. It reads `.env` from `~/.hermes/.env`, **NOT** from `~/.hermes/profiles/default/.env`. Writing tokens/allowlists to `profiles/default/.env` will have NO effect — the bot will reject all users as "Unauthorized".

**Correct locations:**

| Service | HERMES_HOME | .env path |
|---|---|---|
| `hermes-gateway.service` (default) | `/root/.hermes` | `/root/.hermes/.env` |
| `hermes-gateway-youtube.service` | `/root/.hermes/profiles/youtube` | `/root/.hermes/profiles/youtube/.env` |
| `hermes-gateway-coding.service` | `/root/.hermes/profiles/coding` | `/root/.hermes/profiles/coding/.env` |

**To find which .env a running gateway reads:** check the process environment:
```bash
cat /proc/$(pgrep -f "hermes_cli.main gateway" | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep HERMES_HOME
```

**Symptom of wrong .env:** Bot connects to Telegram but logs show:
```
WARNING gateway.run: Unauthorized user: <user_id> (<username>) on telegram
```
This means `TELEGRAM_ALLOWED_USERS` is missing from the .env the gateway actually reads.

**Required entries in the correct .env:**
```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALLOWED_USERS=<user_id>
TELEGRAM_HOME_CHANNEL=<user_id>
```

## Managing Profile Gateways via systemd

Each profile has a systemd service: `hermes-gateway-<profile>.service`.

```bash
# Check status of all profile gateways
systemctl is-active hermes-gateway.service hermes-gateway-youtube.service hermes-gateway-coding.service hermes-gateway-traffic.service

# Restart a specific profile gateway
sudo systemctl restart hermes-gateway-coding.service

# Stop/start
sudo systemctl stop hermes-gateway-coding.service
sudo systemctl reset-failed hermes-gateway-coding.service  # if in "failed" state
sudo systemctl start hermes-gateway-coding.service
```

**Note:** Services in `failed` state need `reset-failed` before `start` will work.

## Verification Steps

After creating a new profile + bot:
1. `hermes profile show <name>` — confirms creation
2. `hermes -p <name> gateway status` — confirms gateway running
3. Send message to new bot — confirms Telegram connectivity
4. Check `~/.hermes/profiles/<name>/sessions/` — confirms isolated storage
5. Ask bot about previous session — should NOT remember default profile context
6. **Check logs** if bot doesn't respond: `tail -20 ~/.hermes/logs/gateway.log` (default) or `tail -20 ~/.hermes/profiles/<name>/logs/gateway.log` (named profile) — look for "Unauthorized user" errors
