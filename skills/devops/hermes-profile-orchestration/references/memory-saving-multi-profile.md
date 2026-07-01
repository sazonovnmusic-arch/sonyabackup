# Memory-Saving Wake-on-Cron for Multi-Profile Hermes

## Problem

Four Hermes profiles (default + coding + youtube + traffic) each run their own `gateway` process via systemd. Each process consumes ~400–550 MB RAM. On a 2–3 GB VPS this totals ~2 GB and leaves almost nothing for actual work.

Root cause: Hermes gateway uses **long-polling** to Telegram. Each profile needs a live process constantly calling `getUpdates`, so stacking profiles stacks memory linearly.

## Solution: Sleep Most, Wake on Demand

Keep only the **default** profile online 24/7 (~450 MB). Spin up secondary profiles via `systemctl` when needed, then shut them down after work or cron windows.

## Who Must Stay Awake

| Profile | Why awake | Memory saved by sleeping |
|---------|-----------|-------------------------|
| default | Catches all messages; routing hub | — |
| youtube | Has cron jobs (daily digest 01:30, weekly scout Mon 05:30) | ~400 MB rest of day |
| coding | No cron; only on human demand | ~470 MB always |
| traffic | No cron; only on human demand | ~420 MB always |

## Quick Commands

```bash
# Start a profile on demand
hermes-wake coding        # alias for systemctl start hermes-gateway-coding

# Stop it when done
hermes-sleep coding       # alias for systemctl stop hermes-gateway-coding

# Check current memory
free -h
```

### Scripts (placed in `/usr/local/bin/`)

**hermes-wake:**
```bash
#!/bin/bash
PROFILE="$1"
shift
SERVICE="hermes-gateway${PROFILE:+-$PROFILE}.service"
[ "$PROFILE" = "default" ] \&\& SERVICE="hermes-gateway.service"

systemctl start "$SERVICE"
for i in $(seq 1 30); do
    if systemctl is-active "$SERVICE" >/dev/null 2>&1; then
        echo "$PROFILE is UP"
        break
    fi
    sleep 1
done

if [ $# -gt 0 ]; then
    HERMES_PROFILE="$PROFILE" HERMES_HOME="/root/.hermes/profiles/$PROFILE" \
      /usr/local/lib/hermes-agent/venv/bin/hermes "$@"
fi
```

**hermes-sleep:**
```bash
#!/bin/bash
PROFILE="$1"
SERVICE="hermes-gateway${PROFILE:+-$PROFILE}.service"
[ "$PROFILE" = "default" ] \&\& SERVICE="hermes-gateway.service"
systemctl stop "$SERVICE"
echo "$PROFILE stopped."
```

## Cron-Based Wake for Scheduled Jobs

Profile `youtube` has nightly cron at 01:30 and weekly at 05:30. Use system `cron.d` to wake it before jobs, sleep after.

**Wake script** (`/usr/local/bin/hermes-wake-youtube.sh`):
```bash
#!/bin/bash
case "$1" in
  start) systemctl start hermes-gateway-youtube ;;
  stop)  systemctl stop  hermes-gateway-youtube ;;
  *)     echo "Usage: $0 {start|stop}"; exit 1 ;;
esac
```

**Cron schedule** (`/etc/cron.d/hermes-youtube-wake`):
```
# Wake 10 min before daily digest, sleep 30 min after
20 1 * * * root /usr/local/bin/hermes-wake-youtube.sh start
0  2 * * * root /usr/local/bin/hermes-wake-youtube.sh stop

# Same for weekly Monday job
20 5 * * 1 root /usr/local/bin/hermes-wake-youtube.sh start
0  6 * * 1 root /usr/local/bin/hermes-wake-youtube.sh stop
```

Restart cron: `service cron restart`

## Result

| State | RAM used | Free |
|-------|----------|------|
| All 4 on | ~2.2 GB | ~300 MB |
| Only default + wake logic | ~1.0 GB | ~1.9 GB |

**Important limitation:** Telegram `getUpdates` polling means a sleeping profile will NOT receive messages until its gateway starts. If you write to `@sonyayoutube_bot` while it's asleep, the bot won't answer until `hermes-wake youtube` runs. For true "wake on message" you'd need **webhook** mode (requires HTTPS domain + reverse proxy), which is heavier to maintain.

Pragmatic compromise: default bot acts as router — ask it to wake others.
