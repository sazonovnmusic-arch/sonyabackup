# Hermes GUI Options Comparison

Session context: 2026-06-21. User has 4 systemd-managed Hermes profiles (default, coding, youtube, traffic) on a single Linux VPS. He wants a unified chat + kanban web interface accessible from his Mac.

## Tier 1 — Built-in: `hermes dashboard` + Hermes Desktop / Hermes One

How it works  
Hermes exposes a web dashboard at a configured port (`hermes dashboard --host 0.0.0.0 --port 9119`). The Hermes Desktop App (macOS) or Hermes One connects to this endpoint with basic auth.

Pros  
- Native, zero extra infrastructure.  
- Shows sessions, memory, and tools.  

Cons  
- **One profile per connection** — you switch profiles by disconnecting and reconnecting to a different port/service.  
- Requires public IP + basic auth (or SSH tunnel) for remote access.  
- **Hermes One** has reported stability/connectivity issues in practice (session 2026-06-21).

Setup checklist  
```bash
# On server
hermes dashboard --no-open --host 0.0.0.0 --port 9119
# Or via systemd unit
```

```bash
# On Mac (SSH tunnel for security)
ssh -N -L 9119:localhost:9119 user@<server-ip>
# Then point Hermes Desktop to http://localhost:9119
```

## Tier 2 — Third-party: Open WebUI / Lobe Chat

How it works  
Open WebUI is a self-hosted ChatGPT-like interface. It speaks the OpenAI API format. Hermes `api_server` platform (when enabled) exposes exactly that format on a local port (default 8642).

Pros  
- Beautiful UI, markdown rendering, conversation history.  
- Runs in any browser on Mac.  
- Easy Docker deployment.  

Cons  
- **Single endpoint** = single profile at a time. To talk to another profile you must change the `OPENAI_API_BASE` env var and restart the container.  
- No native kanban/task view.  

Quickstart command  
```bash
docker run -d -p 3000:8080 \
  -e OPENAI_API_BASE=http://host.docker.internal:8642/v1 \
  -e OPENAI_API_KEY=*** \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

Then browse to `http://<server-ip>:3000` from Mac.

**Important:** `api_server` must be enabled in the target profile's `config.yaml`:
```yaml
platforms:
  api_server:
    enabled: true
    extra:
      port: 8642
      api_key: ''
```

Restart gateway after enabling.

## Tier 3 — Custom: FastAPI mini-app (chat + kanban in one page)

When to use  
When the user explicitly rejects both built-in and third-party options, or needs **all 4 profiles + kanban in one browser window**.

Rough architecture  
- **Backend:** FastAPI (~300 lines) exposing two routes: `/chat/{profile}` (proxies to each profile's `api_server`) and `/kanban` (reads `~/.hermes/kanban.db` directly).  
- **Frontend:** Vanilla JS + CSS grid — left column chat, right column kanban list.  
- **Auth:** HTTP Basic Auth (reuse credentials from dashboard config).  

Pros  
- All profiles in one window.  
- Kanban visible alongside chat.  
- Full control over UX.  

Cons  
- Requires building and maintaining.  
- Not a 5-minute setup.  

Implementation pointers  
- Chat: `fetch('/chat/default', {method:'POST', body:JSON.stringify({messages})})` → proxies to `localhost:8642/v1/chat/completions`.
- Kanban: Read SQLite with `sqlite3`, render rows as cards.
- Profile switch: Dropdown changes the backend port (each profile's `api_server` must use a unique port).

## Decision Tree

```
Does Hermes One work reliably?
├─ YES → Use Hermes Desktop App with SSH tunnel. Done.
└─ NO  → Is multi-profile chat in one window required?
   ├─ YES → Custom FastAPI app (Tier 3).
   └─ NO  → Open WebUI (Tier 2) with manual profile switching.
```

## Reference: Current api_server status check

```bash
# See if api_server is listening
ss -tlnp | grep -E "8642|8650|9119"

# Quick health probe
for port in 8642 8650 9119; do
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:$port/" 2>/dev/null || echo "DOWN"
done
```
