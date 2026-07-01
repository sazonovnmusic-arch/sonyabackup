# AI Workspace Archive & Restore Pattern

Use before big refactors, third-party UI experiments, or pauses.

## Archive
```bash
mkdir -p ~/ai-workspace-archive
cd ~
tar --exclude='ai-workspace/ui/node_modules' \
    --exclude='ai-workspace/bridge/.venv' \
    --exclude='ai-workspace/ui/dist' \
    -czf ai-workspace-archive/ai-workspace-YYYYMMDD-HHMMSS.tar.gz ai-workspace
```

Include in archive folder:
- `README-STATE.md` — current working state, known bugs, how to run.
- `restore.sh` — one-command restore script.

## Restore script template
```bash
#!/usr/bin/env bash
set -e
ARCHIVE="$1"
pkill -f "serve -s dist -l 3000" 2>/dev/null || true
pkill -f "uvicorn main:app --host 0.0.0.0 --port 8123" 2>/dev/null || true
rm -rf ~/ai-workspace
tar -xzf "$ARCHIVE" -C ~
cd ~/ai-workspace/bridge
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ~/ai-workspace/ui
npm install
npm run build
```

## Restart after restore
```bash
cd ~/ai-workspace/bridge && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8123 --log-level info
cd ~/ai-workspace/ui && npx serve -s dist -l 3000 --no-request-logging
```

## Notes
- Do NOT archive `node_modules` or `.venv` — they are large and rebuildable.
- `dist/` is rebuildable too; exclude it to keep archive small.
- Keep workspace.db if it contains important tasks/files; it lives in `bridge/` and is small.
