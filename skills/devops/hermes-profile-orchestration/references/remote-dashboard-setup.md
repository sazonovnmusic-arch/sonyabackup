# Remote Dashboard Setup for Hermes Desktop

Recipe for exposing a server-side Hermes instance to a Hermes Desktop App on another machine.

## Server Side

### 1. Generate secure credentials

```bash
openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24  # username
openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 43  # password
openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 43  # secret
```

### 2. Write to secrets

```bash
cat >> ~/.hermes/.env << 'EOF'
HERMES_DASHBOARD_BASIC_AUTH_USERNAME=<...hmod 600 ~/.hermes/.env
```

> **Do NOT** use the same `.env` as Telegram tokens — keep dashboard auth separate.

### 3. Start dashboard

```bash
# Foreground (for testing)
hermes dashboard --no-open --host 0.0.0.0 --port 9119

# Background via systemd (recommended)
# See references/systemd-multi-profile-units.md for unit template
```

### 4. Verify it's listening

```bash
curl -s http://localhost:9119/api/status | python3 -m json.tool
# Expected: auth_required=true, auth_providers=["basic"]
```

## Client Side (Desktop App)

### Option A: SSH Tunnel (recommended for security)

```bash
# On client machine, in separate terminal:
ssh -N -L 9119:localhost:9119 root@<server-ip>

# In Desktop App:
# Settings → Gateway → Remote URL: http://localhost:9119
# Sign in with basic auth credentials
```

### Option B: Direct Connection (with IP whitelist)

```bash
# In Desktop App:
# Settings → Gateway → Remote URL: http://<server-public-ip>:9119
# Sign in with basic auth credentials
```

> Only use direct connection if firewall restricts access to your client IP.

## Security Notes

- `0.0.0.0` + basic auth = exposed to internet. Acceptable for testing; use Tailscale or firewall for production.
- Dashboard reads `.env` (API keys). Never expose without auth.
- Per-profile remote hosts: each profile can point to its own server in Desktop settings.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` | Dashboard not running or bound to 127.0.0.1 | Check `ss -tlnp \| grep 9119`; use `--host 0.0.0.0` |
| `401 Unauthorized` | Wrong credentials | Re-check `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` / `PASSWORD` |
| Signed out on restart | Missing `HERMES_DASHBOARD_BASIC_AUTH_SECRET` | Set stable secret in `.env` |
| White screen in Desktop | Version mismatch between server and Desktop | Run `hermes update` on both sides |
