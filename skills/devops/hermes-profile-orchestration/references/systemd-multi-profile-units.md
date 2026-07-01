# systemd Units for 4-Profile Hermes Setup

Copy-paste ready unit files for default + youtube + coding + traffic profiles running simultaneously under systemd.

## Main (default) profile

Usually already installed by `hermes gateway install`. If not:

```ini
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli.main gateway run
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## YouTube profile

```ini
[Unit]
Description=Hermes Agent Gateway - YouTube Profile
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment="HOME=/root"
Environment="HERMES_HOME=/root/.hermes/profiles/youtube"
Environment="HERMES_PROFILE=youtube"
Environment="HERMES_GATEWAY_LOCK_DIR=/tmp/locks-youtube"
WorkingDirectory=/root/.hermes/profiles/youtube
ExecStartPre=/bin/sh -c 'rm -f /root/.hermes/profiles/youtube/gateway.pid /root/.hermes/profiles/youtube/gateway.lock'
ExecStart=/usr/local/lib/hermes-agent/venv/bin/hermes gateway run --force
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Coding profile

```ini
[Unit]
Description=Hermes Agent Gateway - Coding Profile
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment="HOME=/root"
Environment="HERMES_HOME=/root/.hermes/profiles/coding"
Environment="HERMES_PROFILE=coding"
Environment="HERMES_GATEWAY_LOCK_DIR=/tmp/locks-coding"
WorkingDirectory=/root/.hermes/profiles/coding
ExecStartPre=/bin/sh -c 'rm -f /root/.hermes/profiles/coding/gateway.pid /root/.hermes/profiles/coding/gateway.lock'
ExecStart=/usr/local/lib/hermes-agent/venv/bin/hermes gateway run --force
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Traffic profile

```ini
[Unit]
Description=Hermes Agent Gateway - Traffic Profile
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment="HOME=/root"
Environment="HERMES_HOME=/root/.hermes/profiles/traffic"
Environment="HERMES_PROFILE=traffic"
Environment="HERMES_GATEWAY_LOCK_DIR=/tmp/locks-traffic"
WorkingDirectory=/root/.hermes/profiles/traffic
ExecStartPre=/bin/sh -c 'rm -f /root/.hermes/profiles/traffic/gateway.pid /root/.hermes/profiles/traffic/gateway.lock'
ExecStart=/usr/local/lib/hermes-agent/venv/bin/hermes gateway run --force
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## InstaModel profile (example of 5th profile)

```ini
[Unit]
Description=Hermes Agent Gateway - InstaModel Profile
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment="HOME=/root"
Environment="HERMES_HOME=/root/.hermes/profiles/instamodel"
Environment="HERMES_PROFILE=instamodel"
Environment="HERMES_GATEWAY_LOCK_DIR=/tmp/locks-instamodel"
WorkingDirectory=/root/.hermes/profiles/instamodel
ExecStartPre=/bin/sh -c 'rm -f /root/.hermes/profiles/instamodel/gateway.pid /root/.hermes/profiles/instamodel/gateway.lock'
ExecStart=/usr/local/lib/hermes-agent/venv/bin/hermes gateway run --force
Restart=on-failure
RestartSec=10
TimeoutStopSec=270

[Install]
WantedBy=multi-user.target
```

## Install all at once

```bash
for profile in youtube coding traffic instamodel; do
  sudo cp /etc/systemd/system/hermes-gateway-$profile.service /etc/systemd/system/
done
sudo systemctl daemon-reload
for profile in youtube coding traffic instamodel; do
  sudo systemctl enable hermes-gateway-$profile.service
  sudo systemctl start hermes-gateway-$profile.service
done
# Verify
systemctl is-active hermes-gateway.service hermes-gateway-youtube.service hermes-gateway-coding.service hermes-gateway-traffic.service hermes-gateway-instamodel.service
```

## Key design decisions

| Element | Why |
|---------|-----|
| `--force` | Bypasses the "already running under systemd" guard. Required because systemd IS running the default gateway, and `hermes gateway run` unconditionally checks this. |
| `HERMES_HOME=<profile_dir>` | Gateway uses `HERMES_HOME/gateway.pid` for the "already running" check. Default is always `~/.hermes`, so without this, a new profile sees main's PID and blocks. |
| `HERMES_GATEWAY_LOCK_DIR=/tmp/locks-<profile>` | Machine-level Telegram token locks live in `<LOCK_DIR>/gateway-locks/`. Without a unique dir, `acquire_scoped_lock()` finds another profile's lock and refuses. |
| `ExecStartPre` cleanup | Stale `gateway.pid` / `gateway.lock` survive after `kill -9`. Cleaning them on every start prevents the recovery loop. |
| `Restart=on-failure` | Auto-restart on crash (OOM, network hiccup, Telegram 5xx). |
| `TimeoutStopSec=270` | **NEW:** Must exceed `agent.restart_drain_timeout` (default 180s) by at least 30s. Prevents systemd SIGKILL mid-drain. If drain_timeout is lowered, adjust proportionally. |

## Managing the fleet

```bash
# Status
systemctl is-active hermes-gateway.service hermes-gateway-youtube.service hermes-gateway-coding.service hermes-gateway-traffic.service hermes-gateway-instamodel.service

# Restart one
sudo systemctl restart hermes-gateway-youtube.service

# Logs
sudo journalctl -u hermes-gateway-coding.service -f

# Stop all extras, keep only main
for svc in hermes-gateway-youtube hermes-gateway-coding hermes-gateway-traffic hermes-gateway-instamodel; do
  sudo systemctl stop $svc.service
done
```

## Pitfall: profile token must be unique

If any profile reuses the default token, systemd will keep restarting it forever. The log shows:

```
Telegram bot token already in use (PID xxx). Stop the other gateway first.
```

Fix: create a new bot via @BotFather and update `~/.hermes/profiles/<profile>/.env`.
