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

## Architecture gotchas (must-know)

### "Hermes Desktop" is CLI, not a GUI app
- Site `hermes-ai.net/desktop/` is **unofficial community page** (disclaimer says "not affiliated with Nous Research").
- Command `hermes desktop` launches a **TUI in terminal**, not a native desktop app like ChatGPT Desktop.
- For a real GUI, users need Open WebUI or another frontend connected via Hermes API Server.

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
