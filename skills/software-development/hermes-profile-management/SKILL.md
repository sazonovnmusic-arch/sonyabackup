---
name: hermes-profile-management
description: "Creating and managing multiple Hermes profiles for different tasks (coding, research, creative). Covers profile isolation, cloning, common pitfalls, and architecture gotchas."
version: 1.0.0
author: Agent
metadata:
  hermes:
    tags: [hermes, profiles, setup, multi-agent, configuration]
---

# Hermes Profile Management

Use this when the user wants to separate memory, skills, settings, or gateway sessions for different types of work.

## Quick commands

```bash
# List existing profiles
hermes profile list

# Create new profile cloned from existing (recommended)
hermes profile create <name> --clone-from <existing>

# Create empty profile
hermes profile create <name>

# Set as default
hermes profile use <name>

# Run command in specific profile
hermes -p <name> chat
hermes -p <name> gateway start
hermes -p <name> gateway install
```

## What gets isolated per profile

| Resource | Isolated? | Notes |
|----------|-----------|-------|
| Config (`config.yaml`) | ✅ Yes | Model, toolsets, display, etc. |
| API keys (`.env`) | ✅ Yes | Can inherit from shell env if missing |
| Skills | ✅ Yes | Copied on `--clone-from`, then diverge |
| Memory (user + agent) | ✅ Yes | Clean slate unless cloned |
| Sessions / history | ✅ Yes | Separate SQLite DB |
| Gateway | ✅ Yes | Each profile can run its own Telegram bot |
| SOUL.md (persona) | ✅ Yes | Customize per profile |

## Typical profile splits

| Profile | Typical model | Use case |
|-----------|---------------|----------|
| `default` | Cost-balanced | General chat, quick questions |
| `coding` | Same or stronger dev model | Code review, scripts, debugging |
| `research` | Strong model + web tools | Deep investigation, synthesis |
| `creative` | Creative-tuned model | Writing, prompts, image gen |

## Reusing existing profiles (pragmatic approach)

When a user says "create X" but an existing profile exists (even a dead one), **prefer reusing over creating**.

```bash
# Check if profile exists
hermes profile list

# Reuse: rename + wipe memory + rewrite SOUL.md
mv ~/.hermes/profiles/<old> ~/.hermes/profiles/<new>
rm -rf ~/.hermes/profiles/<new>/sessions/* \
       ~/.hermes/profiles/<new>/state.db \
       ~/.hermes/profiles/<new>/logs/* \
       ~/.hermes/profiles/<new>/cron/* \
       ~/.hermes/profiles/<new>/cache/*
# Keep: config.yaml, .env (clean old credentials), references/, skills/
# Rewrite: SOUL.md for new persona
```

> **Pitfall:** Creating `hermes profile create X --clone-from Y` duplicates memory, sessions, and bloated state. If the user wants a *clean* persona with the same Telegram bot token — rename + wipe is faster and avoids stale context.

---

## Restarting a hung gateway (real case: instamodel)

**Symptom:** Profile "thinks for a long time" — no response, gateway appears stuck.

**Root cause (instamodel):** Agent got stuck in an infinite loop generating broken bash/python scripts for Pinterest scraping → syntax errors → retries → memory bloated → gateway unresponsive.

**Fix pattern:**

```bash
# 1. Find PID
ps aux | grep -E "PROFILE_NAME" | grep -v grep

# 2. Force-kill
kill -9 PID
sleep 2
ps aux | grep -E "PROFILE_NAME" | grep -v grep || echo "Clean"

# 3. Restart
hermes -p PROFILE_NAME gateway run
```

**Critical:** Use `terminal(background=true)` for gateway — NOT `nohup`, `disown`, or `setsid`. Hermes must track the process.

**Prevention for scraping-heavy profiles:**
- Write working scripts as static files under `~/.hermes/profiles/<name>/scripts/`
- Reference them from skills instead of generating ad-hoc commands
- Monitor memory usage: if memory > 90%, kill + restart

### Profile autonomy rule

When the user says «всё внутри неё пусть происходит» or similar — respect full autonomy:
- No cross-profile delegation for that workflow
- Gateway runs standalone with its own Telegram bot
- Cron, generation, approval, and publishing all stay inside the single profile

## Architecture gotchas (must-know)

### "Hermes Desktop" — two versions exist

1. **Official Hermes Desktop** (Nous Research): native Electron app. Can connect to a **remote backend** via `hermes dashboard`.
   - Remote setup: `hermes dashboard --host 0.0.0.0 --port 9119` + basic auth or OAuth
   - Desktop app connects via WebSocket to `http://<server>:9119`
   - Per-profile remote host supported (each profile can point to its own server)

2. **Community fork** (`fathah/hermes-desktop`, "Hermes One"): standalone app with built-in remote mode via HTTP API + API key on port 8642.
   - Different codebase, not affiliated with Nous Research
   - Supports SSH tunnel mode for secure remote access

### Hermes Dashboard vs Gateway — separate processes

| Process | Purpose | Already running? |
|---------|---------|----------------|
| **Gateway** | Telegram/Discord/Slack bots | Usually yes |
| **Dashboard** | Web UI + Desktop backend | Usually no |
| **API Server** | HTTP API for external clients | Rarely |

> To connect Desktop App to a remote server, you MUST start **dashboard** (or API server) as a separate process. Gateway alone is not enough.

### Local install ≠ same agent
- Installing Hermes on the user's local PC creates a **brand-new agent**.
- It has **zero shared memory** with the server agent (names, preferences, history).
- Skills must be re-copied or re-installed.

### Server agent cannot touch local files directly
- The server agent runs on the Linux host it is deployed to.
- To work with files on the user's personal PC, use one of:
  1. Sync folder to server (Syncthing, SFTP, cloud)
  2. User runs script locally and sends results back
  3. Mount remote directory on the server

## Creating a coding profile (recipe)

```bash
# 1. Create and clone from default
hermes profile create coding --clone-from default

# 2. Verify
hermes profile show coding

# 3. Launch session
hermes -p coding chat
```

The alias `coding` is created at `~/.local/bin/coding`. Add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## References
- Official docs: https://hermes-agent.nousresearch.com/docs/
- CLI reference: `hermes profile --help`
