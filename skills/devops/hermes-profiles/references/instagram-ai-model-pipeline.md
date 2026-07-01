# Instagram AI-Model Content Pipeline

Session-derived recipe for automating an Instagram account with an AI-generated model persona. Covers profile setup, persona design, content generation, approval workflow, and publishing.

## Profile Setup (Reuse vs Create)

**Prefer reusing a dead profile over creating new:**
```bash
# 1. Rename existing unused profile
mv ~/.hermes/profiles/<old> ~/.hermes/profiles/instamodel

# 2. Wipe all memory — critical for clean persona
rm -rf ~/.hermes/profiles/instamodel/sessions/*
rm -f ~/.hermes/profiles/instamodel/state.db
rm -rf ~/.hermes/profiles/instamodel/logs/ ~/.hermes/profiles/instamodel/cache/
rm -rf ~/.hermes/profiles/instamodel/cron/ ~/.hermes/profiles/instamodel/audio_cache/
rm -rf ~/.hermes/profiles/instamodel/image_cache/
rm -f ~/.hermes/profiles/instamodel/channel_directory.json ~/.hermes/profiles/instamodel/auth.json

# 3. Clear old skills (optional)
rm -rf ~/.hermes/profiles/instamodel/skills/*

# 4. Update SOUL.md with AI model persona (see template below)
# 5. Verify model in config.yaml
```

## Persona Design (SOUL.md Template)

```markdown
# AI Instagram Model — [Name]

## Identity
- **Name:** [First Last]
- **Age:** [N]
- **Nationality:** [Country, now living in Country]
- **Appearance:** [Key visual traits for generation prompts]
- **Voice:** [Tone — playful, dry, warm, etc.]
- **Languages:** [Primary for IG, plus quirks]

## Content Themes
- [Theme 1: lifestyle, fashion, fitness, travel]
- [Theme 2]
- [Theme 3]

## Audience
- Target: [Gender, age range]
- Goal: [Growth → monetization path]

## Phased Rollout
- **Phase 1 (now):** SFW Instagram only — growth
- **Phase 2 (later):** Paid subscriptions (Patreon/OF/closed TG) — NSFW
- **Instagram remains SFW teaser** even after Phase 2

## Constraints
- SFW on Instagram always
- No real-person face-swap without consent
- No scraping Pinterest/Instagram/TikTok for refs
- Preview ALL posts in Telegram before publishing
```

## Content Pipeline

1. **Trigger** — cron or manual command
2. **Theme selection** — random from curated list
3. **Prompt generation** — LLM writes image prompt + negative prompt
4. **Image generation** — options:
   - **API:** Replicate/Stability (~$0.002–0.01/photo, fast, zero server load)
   - **Local:** ComfyUI + InstantID/IP-Adapter for consistent face (needs GPU, 3-5 min on CPU)
5. **Caption + hashtags** — LLM generates 150–400 chars + 15–25 hashtags
6. **Telegram preview** — send photo + caption + buttons:
   - `[✅ Постить]` — publish via Graph API
   - `[❌ Отклонить]` — discard
   - `[✏️ Caption]` — regenerate text
7. **Publish** — Instagram Graph API (Business/Creator account only)

## Legal Image Sources (never scrape IG/Pinterest)

| Source | API | License |
|--------|-----|---------|
| Unsplash | Free | Commercial w/ attr |
| Pexels | Free | Commercial |
| Pixabay | Free | Simplified |
| CivitAI | API | CC varies |

## Requirements

| Component | Must Have |
|-----------|-----------|
| IG Account | Creator or Business (Graph API rejects Personal) |
| Facebook Page | Linked to IG account |
| Meta App | Registered + reviewed for publish permissions |
| Telegram Bot | For preview/approval workflow |
| Image Gen | API key (Replicate/Stability) OR local ComfyUI |

## Quick Start

```bash
# Reuse dead profile
mv ~/.hermes/profiles/<old> ~/.hermes/profiles/instamodel
# ... wipe memory (see above) ...

# Or create fresh
hermes profile create instamodel --clone-from default
rm -rf ~/.hermes/profiles/instamodel/sessions/* ~/.hermes/profiles/instamodel/state.db

# Set model (see model-usage skill for cost optimization)
hermes -p instamodel config set model.default kimi-k2.6:cloud
```

## Model Choice for Orchestrator

- **Avoid:** models with high real-world token burn even if cheap per-million
- **Prefer:** models with proven low actual usage (e.g. kimi-k2.6:cloud over gemini-3-flash when the latter shows 5-10x higher session usage in practice)
- See `model-usage-and-performance-optimization` skill for details

## Pitfalls

1. **Graph API rejects Personal accounts** — must be Creator/Business
2. **CPU generation = 3–5 min/photo** — API is faster but costs per image
3. **Consistent face needs InstantID/IP-Adapter or LoRA** — raw txt2img drifts
4. **Instagram flood control** — ~25 posts/day max, spread them out
5. **Shadowban from repetitive content** — vary poses, locations, themes
6. **Face-swap on real people = ToS violation** — only synthetic or licensed photos
7. **Telegram bot token collision** — each profile needs unique bot token
8. **Phase separation** — never post NSFW to Instagram even "accidentally"; keep Phase 2 content off IG entirely
