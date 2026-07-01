# Cross-Profile Gateway Restart (from default to sibling)

## Scenario

User has multiple Hermes profiles running as separate processes. One profile (`instamodel`, `coding`, `youtube`, etc.) hangs or enters an infinite error loop. The user is talking to the `default` profile and wants it to fix the sibling.

## Gateway Self-Preservation Rule

**NEVER restart your OWN gateway from inside.** If the `default` profile tries to restart `default`, it kills itself mid-operation. Always return the command to the user or delegate to another bot.

**Restarting a SIBLING profile is allowed.** The `default` profile can kill and restart `instamodel` because they are separate OS processes with separate PIDs.

## Diagnosis: Is the profile hung or dead?

```bash
# 1. Check if process exists
ps aux | grep -E "instamodel" | grep -v grep

# 2. Check logs for infinite error loops
tail -50 ~/.hermes/profiles/instamodel/logs/gateway.log | grep -E "ERROR|error|Traceback|syntax|can’t open"

# 3. Check for zombie patterns: same error repeating every few seconds
# Example: syntax error in generated bash script → retry → same error → retry
```

## Signs of "infinite error loop" (most common hang)

- Gateway process is alive (PID exists, CPU usage low)
- But bot does not respond to messages
- Logs show the same error repeating (syntax error, failed curl, missing file)
- The profile is stuck inside a tool call retry cycle

**Root cause:** The LLM generated a broken script, the script failed, and the agent keeps regenerating similarly broken scripts. Memory fills up with error context, making each subsequent attempt worse.

## Fix: Hard kill + clean restart

```bash
# Step 1: Kill the hung process
kill -9 <PID>

# Step 2: Verify it's gone
ps aux | grep -E "instamodel" | grep -v grep || echo "Clean"

# Step 3: Start fresh (background, detached)
cd /root && hermes -p instamodel gateway run &
# Or with setsid for full detachment:
setsid bash -c 'cd /root && hermes -p instamodel gateway run' &
```

> **Do NOT use `nohup ... &`** from inside a tool call — Hermes rejects shell-level background wrappers. Use `terminal(background=true)` or `setsid`.

## Prevention: Clean memory + remove broken skills

If the profile keeps hanging on the same task:

1. **Delete generated temp files** that may be poisoning context:
   ```bash
   rm -rf /tmp/pinterest* /tmp/curl_* /tmp/script_*
   ```

2. **Remove broken skills** that contain bad instructions:
   ```bash
   rm -rf ~/.hermes/profiles/instamodel/skills/<broken-skill-name>
   ```

3. **Wipe session state** if memory is full of errors:
   ```bash
   rm -f ~/.hermes/profiles/instamodel/state.db-wal
   # Or full state reset:
   rm -f ~/.hermes/profiles/instamodel/state.db
   ```

4. **Add guardrails to MEMORY.md** so the profile doesn't repeat the mistake

## Communication pattern with user

When user says "[Other profile] hangs / thinks too long / doesn't respond":

1. **Check logs** — confirm it's an infinite loop, not a dead process
2. **Explain the root cause** — "She generated a broken script and keeps retrying"
3. **Ask for permission** — "Kill and restart?"
4. **Execute** — hard kill + clean restart
5. **Report** — "Restarted, PID xxx, clean start"

## Cross-profile file editing

When editing another profile's files (memory, skills, config) from `default`:

```bash
# Use cross_profile=True in patch/write_file
patch cross_profile=True --path ~/.hermes/profiles/instamodel/memories/MEMORY.md ...
```

Or via terminal:
```bash
cat >> ~/.hermes/profiles/instamodel/memories/MEMORY.md << 'EOF'
New memory entry...
EOF
```

## Lesson from this session

Instamodel hung because:
1. Generated bash scripts with syntax errors for Pinterest scraping
2. Each failure added error context to memory
3. Memory filled up (1965/2200 chars)
4. LLM couldn't generate working scripts anymore — death spiral

**Fix applied:**
- Killed PID, restarted clean
- Deleted temp files (`/tmp/pinterest*`)
- Removed broken skill (`ai-instagram-model`)
- Added hard rules to MEMORY.md (Pinterest-only, proxy-required, IP-rotation)
