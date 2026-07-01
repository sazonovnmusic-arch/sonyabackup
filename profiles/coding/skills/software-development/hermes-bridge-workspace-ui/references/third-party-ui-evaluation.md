# Evaluating third-party agent UIs for Hermes

Use this reference when the user asks "maybe use a ready-made UI like AionUi?" It records what was checked and the practical outcome, so future sessions don't repeat the same experiment blindly.

## Candidates reviewed

### 1. AionUi (iOfficeAI/AionUi) — 29K stars

- Claims direct Hermes Agent support.
- Multi-agent (5 profiles simultaneously), WebUI, Telegram/Lark/DingTalk/WeChat.
- Electron-based desktop app, but also has a `webui:remote` script.
- **Practical issue:** the repo ships as source only. Running `webui:remote` requires building `out/renderer` and the server bundle first (`bun run build:renderer:web`, `node scripts/build-server.mjs`). On a headless VPS the build may need extra native dependencies (Electron, libicu, etc.) and is not guaranteed to finish quickly.
- **Verdict:** promising if you can spend time on the build, but not a 5-minute drop-in on a headless server. The user's workflow is browser-over-IP, so it must run in web mode.

### 2. ClawFleet (clawfleet/ClawFleet) — 164 stars

- Docker-isolated agents, fleet management, cyberpunk dark dashboard.
- Too small and raw for production; not evaluated further in this session.

### 3. Hermes built-in dashboard

- `hermes dashboard --port 9119`.
- Admin/config panel, not a multi-agent card/chat UI.
- Not a replacement for the workspace UI.

## Decision guide

| Need | Choice |
|------|--------|
| Quick working browser UI over Hermes, full control over design | Custom React + Bridge (the main project). |
| Ready unified interface with multi-agent + integrations + willingness to fight the build | AionUi. |
| Docker fleet / mass instance management | ClawFleet (evaluate stability first). |
| Just config/session admin | `hermes dashboard`. |

## Borrow ideas, don't always deploy

If a third-party UI almost fits but cannot be made to run quickly on the user's headless VPS, **do not keep fighting the build for hours**. Instead:

1. Identify the specific mechanic that would improve the custom UI (e.g., instant push delivery of assistant messages, a clean Markdown layout, a card-based agent dashboard).
2. Extract that idea and implement it in the custom React + Bridge stack.
3. Preserve the user's existing visual style, profile list, and workflow.

In this session AionUi's chat used WebSocket/SSE push, and ChatGPT's message layout was referenced for typography. Both ideas were adapted into the custom UI instead of replacing it.

## Backup before experiments

When trying a third-party UI, always back up the current custom UI/Bridge first:

```bash
cp -r ~/ai-workspace/ui ~/ai-workspace/ui_backup
cp -r ~/ai-workspace/bridge ~/ai-workspace/bridge_backup
```

This lets you revert instantly if the experiment fails or the user wants the old UI back.

## Environment constraints

- Hermes lives on a headless VPS.
- User opens the UI in a browser by IP.
- Electron-only apps are impractical unless they expose a web endpoint or are rebuilt as a web app.
- Do **not** delete or modify Hermes profiles, cron jobs, skills, or configs while testing third-party tools.

## What was actually tried (session 2026-07-01)

### AionUi

Cloned to `/opt/AionUi`, installed `bun` and dependencies (`bun install` — 3544 packages). Running `bun run webui:remote` starts `electron-vite build` to produce `out/renderer`, but on a headless VPS the build hangs at the renderer production bundle step (no output after Vite warnings for many minutes, process CPU drops to 0%). It did not finish in 5 minutes of foreground time; the background process also never reached "AionUi WebUI is ready".

Likely blockers:
- Renderer build is heavy and may need more CPU/memory or native deps than available.
- The separate `aioncore` backend binary may be missing; the Dockerfile expects `bun run build:renderer:web` and `node scripts/build-server.mjs` first.

Conclusion: AionUi is **not a quick drop-in** on this VPS. Revisit only with a beefier box or local desktop build.

### ClawFleet

Cloned to `/opt/ClawFleet`. It is a Go-based Docker fleet manager, not a chat UI. Its web dashboard shows instance cards, VNC/NoVNC desktop access, and fleet controls. There is no built-in chat interface — users interact with agents through the agent's own gateway/UI inside the container. ClawFleet is useful for fleet ops, not as a chat replacement.

## Notes

AionUi's `webui:remote` script exists, but it expects pre-built artifacts:

```
out/renderer/          # frontend build
dist-server/           # backend bundle
aioncore binary        # or bundled backend
```

If you want to retry AionUi later, start with:

```bash
cd /opt/AionUi
export PATH="$HOME/.bun/bin:$PATH"
bun run build:renderer:web
node scripts/build-server.mjs
AIONUI_HOST=0.0.0.0 AIONUI_ALLOW_REMOTE=true AIONUI_PORT=3001 bun run webui:prod:remote
```

Monitor for missing `aioncore` binary or libicu errors.
