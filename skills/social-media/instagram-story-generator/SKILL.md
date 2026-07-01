---
name: instagram-story-generator
description: Generate professional Instagram Stories with text overlay, glow effects, gradients, and proper 9:16 formatting using local Python/Pillow. Avoids unreliable img2img APIs.
triggers:
  - instagram story
  - insta story
  - story generator
  - наложить текст на фото для инсты
  - сделать сторис
  - instagram text overlay
  - photo text overlay instagram style
  - glow text on image
  - gradient text overlay
---

# Instagram Story Generator

## When to use this skill

User wants Instagram Stories (9:16) with professional text overlay — glow, gradient, shadows, modern fonts. This skill covers **local generation** via Pillow, which is fast, free, and reliable. Do NOT attempt API-based img2img unless user explicitly provides a working token.

## Key insight from sessions

**No good open-source Instagram Story generators exist on GitHub.** Searched extensively — all repos are either:
- Basic meme generators (white text on black panel)
- HTML templates requiring browser rendering
- Scrapers/downloader tools
- ComfyUI nodes (too complex to automate)

**Best approach: build locally with Pillow.**

## Generator variants

Two approaches depending on desired output style:

### Approach A: Bubble/rectangle style (recommended for CTA)

White/red rounded-rectangle bubbles like real Instagram Stories. Fast, clean, readable.

**Script:** `/root/insta_story_v6.py`

```bash
python3 /root/insta_story_v6.py <input_photo> <output.png>
```

**Key settings:**
- `BUBBLE_W = 520`, `BUBBLE_H = 90` — fixed size for both bubbles
- `radius = 20` — moderate corner rounding (not pill shape)
- `font_size = 46–52` — smaller than you think
- No tilt (`tilt = 0`) unless user explicitly asks

**Result:** Two same-width rectangles, centered text, soft shadow.

### Approach B: Gradient glow text (artistic)

Text with vertical gradient (white→pink→purple) and pink glow. More decorative, less like native Stories UI.

**Script:** `/root/insta_story_generator.py` (legacy v1)

```bash
python3 /root/insta_story_generator.py <input_image> <output_path> [preset]
```

**Presets:** `wanna_chat`, `flirty`

**Use when:** user wants artistic text overlay, not native Stories look.

## Fonts

Required fonts (auto-downloaded on first run):
- **Montserrat** (`/root/insta_fonts/Montserrat-ExtraBold.ttf`)
- **Montserrat Bold** (`/root/insta_fonts/Montserrat-Bold.ttf`)
- Fallback: Lato Heavy (system)

**Note:** Montserrat does NOT support emoji. If user requests emoji in text, either:
1. Install NotoColorEmoji: `curl -sL "https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf"`
2. Or simply omit emoji from overlay (recommended — cleaner look)

## Pitfalls

| Problem | Cause | Solution |
|---------|-------|----------|
| `images do not match` error | Layer sizes mismatch during alpha_composite | Use temp canvas: `temp = Image.new('RGBA', canvas.size); temp.paste(layer, (x,y)); canvas = Image.alpha_composite(canvas, temp)` |
| Text not centered | `draw.text()` origin at top-left of bbox | Calculate `tx = (width - tw) // 2 - bbox[0]` to account for font bearings |
| Glow too weak | Single-pass glow | Use multi-pass: outer glow (80px radius, blur 15) + inner glow (40px, blur 8) |
| Slow rendering | Per-pixel `putpixel()` loops | Acceptable for 1–2 text lines; for batch processing consider numpy vectorization |
| **Bubbles different widths** | Auto-sizing to text length | Use **fixed width/height** for all bubbles (e.g. `BUBBLE_W = 520, BUBBLE_H = 90`) |
| **Font too large** | Using 80–90px like posters | Instagram Stories text is smaller: **44–52px** for main text, **46–54px** for CTA |
| **Tilt breaks alignment** | Rotation with `expand=True` | Use `expand=False` to keep canvas, or **skip tilt entirely** for clean look |
| **Pillow rounded_rectangle is uneven** | Different colors = slightly different sizes | Pre-render to **fixed-size canvas**, then paste. Or use manual `draw.ellipse()` + `draw.rectangle()` |
| **Emoji shows as square** | Montserrat has no emoji glyphs | Either install NotoColorEmoji font, or **avoid emoji in overlay text** |
| **Triptych input photos** | Source image is 3 stacked panels | Resize/crop to single 9:16 frame FIRST, then overlay text. Do NOT output triptych unless requested |
| **Shadow blur crops edges** | Blur radius eats into bubble | Add 30px padding around bubble before applying GaussianBlur |

## API providers tested (avoid unless user confirms tokens)

| Provider | img2img support | Result |
|----------|-----------------|--------|
| OpenAI Images API | ❌ No | Only text-to-image; `reference` parameter rejected |
| FAL.ai (FLUX Redux) | ✅ Yes | Requires paid balance; user account locked on test |
| Replicate | ✅ Yes | Requires valid token; user's tokens returned 401 |
| Pollinations.ai | ❌ Partial | Ignores image reference, generates abstract art |
