---
name: hermes-profiles
description: Manage isolated Hermes profiles with clean memory, separate Telegram bots, and lazy skill loading for distinct workflows (coding, content, admin, etc.)
version: 1.0.0
author: agent
tags: [hermes, profiles, isolation, multi-agent, gateway, telegram]
---

# Hermes Profile Isolation Workflows

When a user wants to keep coding, content creation, personal chat, and other domains strictly separated, create dedicated profiles instead of polluting the default profile. Each profile gets its own memory, sessions, skills, and (optionally) its own Telegram bot.

## 1. Creating an Isolated Profile

### Step-by-step

1. Create profile cloned from default so API keys (`.env`) and base config are inherited:
   ```bash
   hermes profile create <name> --clone-from default
   ```

2. **Wipe cloned session/memory state** so the new profile starts with a blank slate:
   ```bash
   rm -f ~/.hermes/profiles/<name>/state.db
   rm -rf ~/.hermes/profiles/<name>/sessions/*
   ```

   > Pitfall: If you skip this step, the new profile inherits old sessions and memory from `default`, defeating the purpose of isolation.

3. Customize `.env` or `config.yaml` if needed (model, toolsets, etc.).

### Why not `--clone-all`?

`--clone-from default` copies `.env` (API keys) and base config, but not the session store, making it the sweet spot for "same keys, clean memory".

## 2. Dedicated Telegram Bot per Profile

### Getting a token

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → choose name → receive token.

2. Write the token into the profile's `.env`:
   ```bash
   hermes -p <name> config env-path   # shows path
   # Edit TELEGRAM_BOT_TOKEN=...
   # Edit TELEGRAM_ALLOWED_USERS=<your_user_id>
   ```

3. **Clean stale duplicate tokens** before first launch:
   ```bash
   grep -n "TELEGRAM_BOT_TOKEN" ~/.hermes/profiles/<name>/.env
   # If there are multiple lines, remove all but the desired one:
   # sed -i '<line_num>d' ~/.hermes/profiles/<name>/.env
   ```

   > Pitfall: Cloning from `default` sometimes leaves a second `TELEGRAM_BOT_TOKEN` line (e.g. at line 474) alongside the newly patched one. This causes silent collision or the wrong bot connecting.

4. Launch gateway:
   ```bash
   hermes -p <name> gateway run
   ```

   Or background:
   ```bash
   hermes -p <name> gateway run &   # then disown / nohup
   ```

### Pitfall: token collision

Each Telegram token can only be used by **one running gateway** at a time. If you see:

```
Telegram bot token already in use (PID xxx). Stop the other gateway first.
```

check that no other profile is using the same token. Use unique tokens per profile.

## 3. Lazy Skill Loading vs Eager Loading

Instead of copying all 78 skills into every profile (memory bloat), let the agent load skills on demand inside the session:

- **In chat / Telegram:** `/skill <name>` or mention the skill in the prompt
- **In CLI:** `hermes -s <name> chat`
- **In code:** `skill_view(name=...)` programmatically

This keeps profiles lightweight. Only preload truly universal skills (e.g., `hermes-agent`) in `config.yaml`.

## 4. Choosing the Right Isolation Level

| Approach | When to use |
|----------|-------------|
| **New profile + new bot** | Distinct domain with its own memory (coding, YouTube, admin) |
| **New profile, same bot** | Same chat thread, but sessions isolated |
| **`delegate_task`** | One-off subtask inside the same session; temporary, not durable |
| **Spawned `hermes` process** | Long-running autonomous mission, fully independent |

## 5. Profile Lifecycle Commands

```bash
hermes profile list                # show all
hermes profile show <name>         # inspect
hermes -p <name> config edit       # tweak model, toolsets
hermes -p <name> gateway status    # is the bot alive?
hermes -p <name> gateway restart   # reload after config change
```

## 6. Memory Isolation Checklist

After cloning a profile intended to be "clean":

- [ ] `state.db` deleted or sessions table empty?
- [ ] `.env` token unique (not reused by another profile)?
- [ ] **No duplicate `TELEGRAM_BOT_TOKEN` lines in `.env`?**
- [ ] `TELEGRAM_ALLOWED_USERS` set correctly?
- [ ] `model.default` adjusted if needed?
- [ ] No `SOUL.md` bleed from default personality?

## 7. Profile Runtime Modes (systemd vs manual)

Hermes profiles can run as **standalone manual processes** or as **systemd services**. Both are valid; the user chooses per their infrastructure.

| Mode | How to start | Pros | Cons |
|------|-------------|------|------|
| **Manual** | `hermes -p <name> gateway run` | Quick, no root needed | Dies on logout, needs watchdog |
| **systemd --user** | `hermes -p <name> gateway install` | Auto-restart, survives reboot | May fail in containers (dbus) |
| **systemd system-wide** | Custom unit per profile | Full reliability, `Restart=always` | Needs root, one unit per profile |

**Real-world setup (4 profiles, one server):**
```bash
# Each profile has its own systemd service
systemctl status hermes-gateway-default
systemctl status hermes-gateway-coding
systemctl status hermes-gateway-youtube
systemctl status hermes-gateway-traffic
```

> In this mode, all profiles share the **same host filesystem** but have **isolated processes**. Cross-profile communication is NOT automatic — see section 8.

### Starting a systemd-managed profile (correct way)

When a profile has a systemd unit, **always prefer `systemctl`** over manual `hermes gateway run`:

```bash
# Check status first
systemctl status hermes-gateway-<name>

# If failed/inactive — start via systemd
systemctl enable hermes-gateway-<name>
systemctl start hermes-gateway-<name>

# Verify
systemctl status hermes-gateway-<name> | grep "Active:"
```

> **Pitfall:** Running `hermes -p <name> gateway run` manually when a systemd unit exists creates **two conflicting processes**. systemd will eventually kill the manual one, or both will fight for the Telegram token. Always use `systemctl` for systemd-managed profiles.

### Restarting a failed systemd profile

```bash
systemctl restart hermes-gateway-<name>
# Wait 5 seconds, then verify:
systemctl status hermes-gateway-<name> | head -5
```

If restart keeps failing, check logs:
```bash
journalctl -u hermes-gateway-<name> -n 50 --no-pager
```

### Persistent "typing..." status in Telegram (no pending request)

**Symptom:** User opens Telegram chat and sees "typing..." indicator, but they haven't sent any message. The indicator persists.

**Root cause:** Multiple gateway processes running simultaneously for the same profile. Telegram receives overlapping "typing" events from different processes.

**Diagnosis:**
```bash
# Look for duplicate gateway processes for the same profile
ps aux | grep -i hermes | grep -v grep
```

Expected: one gateway process per profile.
If you see multiple `hermes gateway run` lines for the same profile, they are conflicting.

**Common sources of duplicates:**
1. Manual `hermes gateway run` launched while systemd unit is already active
2. systemd auto-restarted a dead process, but the old one didn't fully die
3. Watchdog script spawned a second instance before the first fully exited

**Fix:**
```bash
# 1. Identify all PIDs for the target profile
ps aux | grep -E "hermes.*instamodel" | grep -v grep

# 2. Kill all of them
kill -9 <PID1> <PID2>

# 3. If systemd-managed, let it restart cleanly
systemctl restart hermes-gateway-instamodel.service

# 4. Verify only one process remains
ps aux | grep -E "hermes.*instamodel" | grep -v grep
```

> **Do NOT explain this away as "normal behavior"** when the user complains. Persistent typing without a request is a bug.

---

## Diagnosing a Slow / Sluggish Profile Bot

**Symptom:** Bot responds but with large delays (seconds to minutes). User says "чё она так долго думает" or similar.

**Quick diagnosis commands:**
```bash
# 1. Check service status
systemctl status hermes-gateway-<name>

# 2. Look at recent logs (last 2 hours)
journalctl -u hermes-gateway-<name> --since "2 hours ago" -n 200 --no-pager

# 3. Check running processes
ps aux | grep -i hermes | grep -v grep

# 4. Check context bloat
du -sh ~/.hermes/profiles/<name>/
```

**Most common root causes (in order of frequency):**

| Symptom | Likely cause | Fix |
|---|---|---|
| Log shows `flood control, waiting Xs` | Telegram rate limiting | `systemctl restart` resets the window |
| Repeating tool errors (`memory`, `skill_manage`, `execute_code`) | Agent stuck in a tool-failure retry loop | Restart gateway, then fix the broken skill/memory |
| No errors, just slow responses | Heavy model (MoE >200B) on shared infra | Switch to lighter model (`deepseek-v4-flash`, `gemini-3-flash`) |
| `Connection error` / API timeout | Provider endpoint down | Swap provider or base_url |
| High CPU, low RAM left | Context bloat or stuck loop | Restart + prune sessions |

**Real-world example from instamodel profile (2026-06-24):**
- Logs showed `flood control, waiting 277.0s` repeatedly
- Plus `memory` errors (`Unknown action 'None'`), `skill_manage` mismatches, `execute_code` font failures
- Root cause: bot was in a tool-failure loop that also flooded Telegram with retry messages
- Fix: `systemctl restart hermes-gateway-instamodel.service` — immediate recovery

See `references/profile-slow-response-diagnosis.md` for full transcript.

### Cleaning stale gateway locks after hard kill

If a gateway was killed with `kill -9` or crashed:
```bash
rm -f ~/.local/state/hermes/gateway-locks/*.lock
rm -f ~/.hermes/profiles/*/gateway.pid ~/.hermes/profiles/*/gateway.lock
systemctl --user reset-failed hermes-gateway-<name>
```

---

## 8. Cross-Profile Communication Limitations

When profiles run as **separate processes** (manual or systemd), `delegate_task` is **profile-local only**:

| Tool | Works across profiles? | Why |
|------|------------------------|-----|
| `delegate_task` | ❌ No | Subagent spawns inside the SAME process |
| `kanban` | ❌ No (default) | SQLite is per-profile unless shared DB |
| `cronjob` | ❌ No | Cron scheduler is per-process |
| **Shared files** | ✅ Yes | All profiles on same machine → same disk |
| **Telegram fwd** | ✅ Yes | Manual or bot-to-bot message |
| **Webhook** | ✅ Yes | If configured per profile |

**Practical pattern:** Profile `coding` generates code → writes to `/shared/results.md` → profile `default` reads it.

---

## 9. Gateway Watchdog / Auto-Restart

Telegram bots die (SIGTERM, OOM, high load). A simple bash watchdog keeps them alive.

### Critical: One active gateway per profile

Hermes maintains a file lock (`gateway.lock`) inside each profile. **Only ONE `hermes -p <name> gateway run` can hold the lock at a time.** If a second instance tries to start, it exits immediately—often silently or with a confusing `SIGTERM` entry in the newest log file while the real running gateway keeps writing to the older log.

**Check before launching:**
```bash
# Correct way to check if a profile gateway is alive
pgrep -f "hermes -p <name> gateway" && echo "RUNNING" || echo "DEAD"
```

> **Do NOT rely solely on `ls -lt ~/.hermes/profiles/<name>/logs/`**. Each failed start attempt creates a fresh log file, so the newest file may belong to a dead process.

**Safe restart pattern:**
```bash
# 1. Kill any existing instance for this profile
pkill -9 -f "hermes -p <name> gateway"
sleep 2

# 2. Verify it's really gone
pgrep -f "hermes -p <name> gateway" || echo "CLEAR"

# 3. Start fresh
hermes -p <name> gateway run
```

**Background / detached start:**
```bash
setsid bash -c 'hermes -p <name> gateway run > ~/.hermes/profiles/<name>/logs/gateway-$(date +%Y%m%d-%H%M%S).log 2>&1' &
```

Or use `subprocess.Popen(..., start_new_session=True)` from Python when launching programmatically.

### Conflicts with global systemd `hermes-gateway.service`

There may be a **system-wide** systemd unit at `/etc/systemd/system/hermes-gateway.service` that runs `hermes gateway run` (no `-p` flag, i.e. the `default` profile). This unit is completely separate from profile-specific gateways, but it can consume resources or cause confusion when diagnosing why a bot won't start.

Check it:
```bash
systemctl status hermes-gateway --no-pager | head -10
```

Profile gateways are NOT managed by this unit—they must be started manually or via per-profile watchdog scripts.

---

Telegram bots die (SIGTERM, OOM, high load). A simple bash watchdog keeps them alive:

```bash
cat > ~/.hermes/profiles/<name>/watchdog.sh << 'EOF'
#!/bin/bash
LOG=~/.hermes/profiles/<name>/watchdog.log
while true; do
    if ! pgrep -f "hermes -p <name> gateway" > /dev/null; then
        echo "$(date): Gateway down, restarting..." >> "$LOG"
        nohup $(which hermes) -p <name> gateway run >> ~/.hermes/profiles/<name>/gateway.log 2>&1 &
        sleep 10
    fi
    sleep 60
done
EOF
chmod +x ~/.hermes/profiles/<name>/watchdog.sh
```

Launch once per boot (or via cron `@reboot`):
```bash
nohup ~/.hermes/profiles/<name>/watchdog.sh &
```

> Note: `systemctl --user` often fails in containers (`Failed to connect to bus`). The nohup watchdog is the portable fallback.

### Reading the watchdog log
```bash
tail -f ~/.hermes/profiles/<name>/watchdog.log
```

---

## 8. SIGTERM at High Load (OOM/Systemd Killer)

When the server is under heavy load (CPU high, many gateways running), systemd or the OOM killer may send SIGTERM to gateway processes. This manifests as:

```
Received SIGTERM — initiating shutdown
Shutdown context: signal=SIGTERM under_systemd=yes loadavg_1m=4.78
```

**Symptoms:**
- Gateway dies unexpectedly even though it was working fine
- Happens during peak hours or when running multiple bots + heavy model queries
- Process simply disappears; watchdog log shows "Gateway down, restarting"

**Mitigation:**
1. **Watchdog script** (see section 7) — already the best defense; it catches the death within 60 seconds and restarts.
2. **Spread load** — avoid running all 4 bots + heavy `execute_code` tasks simultaneously.
3. **Monitor loadavg** — if `loadavg_1m` consistently > 3.0, consider upgrading the server or staggering cron jobs.
4. **Restart stagger** — don't restart all gateways at the same time; spread by 30-60 seconds.

> Note: `systemd --user` auto-restart (`Restart=always`) rarely works in containerized environments. The standalone bash watchdog is more reliable.

## References

- `references/profile-gateway-lock-conflict.md` — error transcript and fix when two profiles share a token
- `references/gateway-token-collision.md` — error transcript and fix for duplicate token lines in `.env`
- `references/instagram-ai-model-pipeline.md` — full automation recipe for IG AI-model content generation and posting
- `references/cross-profile-gateway-restart.md` — diagnosing and restarting hung sibling profiles (infinite error loops, broken script retries)
