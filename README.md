# Hermes Backup

Automated backup of Hermes configuration, skills, profiles, scripts, and memories.

**⚠️ This repo does NOT contain secrets.**
Tokens, API keys, and `.env` files are excluded via `.gitignore`.

## Structure

- `config.yaml` — main Hermes config
- `profiles/` — isolated profile configs (default, coding, youtube, traffic, instamodel)
- `skills/` — custom skills
- `scripts/` — helper scripts
- `memories/` — persistent memory files
- `cron/jobs.json` — scheduled cron jobs
- `SOUL.md` — agent persona
