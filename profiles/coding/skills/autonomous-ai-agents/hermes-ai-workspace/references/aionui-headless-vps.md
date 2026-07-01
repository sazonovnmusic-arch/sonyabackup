# AionUi Headless WebUI on a VPS

Quick recipe for running the AionUi Electron app in headless WebUI mode on a Linux VPS where Hermes Agent is already installed.

## Why headless?

AionUi is an Electron desktop app, but it supports `--webui --remote` flags that start an embedded web server. On a server without a monitor, use Xvfb as a virtual display.

## Prerequisites

- Linux x86_64 VPS
- Hermes Agent installed and globally available in PATH (`which hermes` succeeds)
- ~1 GB free disk space (`.deb` is ~400 MB)
- ~2 GB RAM recommended for Electron + backend

## Install

```bash
# 1. Check resources
free -h && df -h /

# 2. Install virtual display dependencies
apt-get update
apt-get install -y xvfb libnotify4 xdg-utils libsecret-1-0

# 3. Download latest release
curl -L -o /tmp/AionUi.deb \
  "https://github.com/iOfficeAI/AionUi/releases/latest/download/AionUi-linux-amd64.deb"

# 4. Install
dpkg -i /tmp/AionUi.deb
apt-get install -f -y
```

The app is installed under `/opt/AionUi/AionUi`. The bundled AionCore backend lives at:

```
/opt/AionUi/resources/bundled-aioncore/linux-x64/aioncore
```

## Start headless WebUI

```bash
cd /opt/AionUi
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
  /opt/AionUi/AionUi --webui --remote --no-sandbox
```

Default ports:
- **25808** — production WebUI (`--webui`)
- **25809** — dev WebUI (`bun run webui`)
- **33000** — when `AIONUI_PORT` is used in standalone CLI

Verify it is listening:

```bash
ss -tlnp | grep 25808
curl -sI http://localhost:25808
```

## Reset admin password

Fresh install needs an admin user. AionUi seeds one automatically; query/reset via API:

```bash
# Check setup state
curl -s http://localhost:25808/api/auth/status

# Reset password
curl -s -X POST http://localhost:25808/api/webui/reset-password
# {"success":true,"data":{"new_password":"..."}}

# Confirm username
curl -s http://localhost:25808/api/auth/internal/users/system
# {"success":true,"data":{"username":"admin",...}}
```

## Connecting Hermes inside AionUi

1. Open `http://SERVER_IP:25808` in a browser.
2. Log in with the admin credentials.
3. Go to Settings / Agents / Local Agents.
4. Add or enable **Hermes Agent**. AionUi should detect `hermes` in PATH and run `hermes acp` as the ACP backend.
5. If it does not detect automatically, provide the command:
   ```
   hermes acp
   ```

## Safe cleanup before install

If disk space is tight, you can safely delete development caches before installing AionUi:

```bash
rm -rf /root/.cache/ms-playwright
rm -rf /root/.npm/_cacache
rm -rf /root/.cache/pip
rm -rf /opt/AionUi/node_modules   # if a source clone exists
rm -rf /opt/AionUi/.git           # source history, not needed for .deb
```

**Never delete:**
- `~/.hermes/profiles/*` — Hermes profiles and state
- `~/ai-workspace-archive/*` — project archives the user asked to keep

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Port 25808 not listening | Check that Xvfb is installed and `xvfb-run` is used. |
| Blank page / JS errors | Use a modern browser; AionUi uses Arco Design + React. |
| Cannot log in | Run the `reset-password` API call again. |
| Hermes not detected | Verify `which hermes` works in the shell, then manually set command to `hermes acp`. |
| High RAM usage | Electron headless still uses 300–800 MB. Consider limiting concurrent agents. |
