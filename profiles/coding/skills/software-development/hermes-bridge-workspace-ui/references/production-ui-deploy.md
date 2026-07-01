# Production UI deployment for Hermes Bridge + React

When the Vite development server becomes unstable (restarts, crashes, or is killed by the host), switch to a production static build served by `serve` or nginx. This note covers the exact command sequence and the single most common mistake that makes the agent list disappear.

## The symptom

After `npm run build` and `npx serve -s dist -l 3000`:
- The page loads.
- The agent/profile sidebar is empty.
- Welcome screen shows "Выберите агента" forever.
- Browser Network tab shows 404 on `/api/profiles`.

Root cause: `serve` serves static files only. Relative API calls like `fetch('/api/profiles')` go to port 3000, not to the FastAPI Bridge on port 8123.

## Fix 1 — absolute API base (quickest)

Set the API base to the Bridge URL before building:

```jsx
// ui/src/App.jsx
const API = 'http://<bridge-host>:8123/api'
```

Then build and serve:

```bash
cd ~/ai-workspace/ui
npm run build
npx serve -s dist -l 3000 --no-request-logging
```

If the Bridge runs on the same host as the browser, replace `<bridge-host>` with the public IP or `localhost`. For an external user, use the public IP/domain.

## Fix 2 — nginx reverse proxy (recommended for public access)

Route both UI and API through one origin:

```nginx
server {
    listen 80;
    server_name ai-workspace.example.com;

    location / {
        root /root/ai-workspace/ui/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8123/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then the React app can keep `const API = '/api'` because the browser sends all `/api/*` requests through nginx to the Bridge.

## Fix 3 — Vite preview (local testing only)

```bash
cd ~/ai-workspace/ui
npm run build
npx vite preview --host 0.0.0.0 --port 3000
```

`vite preview` honors `vite.config.js` proxies, but it is not meant for production load.

## Background command with logging

Run `serve` in the background and keep logs for diagnostics:

```bash
cd ~/ai-workspace/ui
nohup npx serve -s dist -l 3000 > ui-server.log 2>&1 &
disown
```

Or use a process manager:

```bash
pm2 start --name ai-workspace-ui "npx serve -s dist -l 3000 --no-request-logging" --cwd ~/ai-workspace/ui
```

## JSX literal `>` warning

While editing the welcome screen, text like `>_` must be escaped:

```jsx
// wrong — Vite/esbuild warns "The character ">" is not valid inside a JSX element"
<div>>_</div>

// correct
<div>&gt;_</div>
```

The warning does not always crash the build, but it can break HMR and leave the dev server in a bad state.

## Verification

After switching to production mode, open the browser's Network tab and confirm:
- `GET /api/profiles` returns 200 with a JSON array of profiles.
- The sidebar renders initials/avatars for each profile.
- `GET /api/agents/status` returns 200 with status objects keyed by `profile`.

If either call 404s, check whether the request URL points at the Bridge host and port, not the static UI server.

## Quick restart recipe

When you patch the UI, always rebuild and restart the static server:

```bash
cd ~/ai-workspace/ui
npm run build
# kill old serve on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null
# start new
npx serve -s dist -l 3000 --no-request-logging
```

For a background process, use `pm2 reload ai-workspace-ui` or kill/restart the `nohup` process.
