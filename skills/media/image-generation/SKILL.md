---
name: image-generation
description: Image generation, img2img, and text overlay processing for social media (Instagram Stories, etc.) across multiple providers and local tools.
version: 1.0
tags: [image, img2img, generation, overlay, text, instagram, stories, api, providers]
---

# Image Generation & Processing

Comprehensive guide for generating images, img2img transformations, and adding text overlays for social media (Instagram Stories, etc.) across multiple providers and local tools.

## When to use this skill
- Need to generate images from text (text-to-image)
- Need to transform existing images (img2img, style transfer)
- Need to add Instagram-style text overlays (glow, gradient, fonts)
- Need to choose a provider based on cost, speed, or features
- Troubleshooting image generation API failures

## Providers

### FAL.ai ⭐ RECOMMENDED (fastest, best quality)
- **API:** `https://fal.run/fal-ai/<model>`
- **Models:** `flux-pro`, `flux-pro/v1.1`, `flux-pro/v1.1-ultra`, `flux-schnell`, `flux-redux` (img2img)
- **Auth:** `Authorization: Key <fal_key>` (format: `uuid:hexstring`)
- **Img2img:** `image_url` + `prompt` + `strength` (0.0-1.0)
- **Cost:** ~$0.02-0.08 per image
- **Speed:** 1-5 seconds
- **Caveat:** Requires balance. Returns `403 User is locked` when exhausted.

### Replicate (good for testing, free tier available)
- **API:** `https://api.replicate.com/v1/predictions`
- **Models:** `black-forest-labs/flux-schnell`, `stability-ai/sdxl`, `tencentarc/photomaker`
- **Auth:** `Authorization: Token <token>` (format: `r8_...`)
- **Img2img:** `image` + `prompt` + `strength` in `input` field
- **Cost:** ~$0.01-0.10 per run (GPU time)
- **Speed:** 10-30 seconds
- **Caveat:** Free tier is $5. Need valid token — `401` means invalid/expired.

### OpenAI (DALL-E, GPT-Image)
- **API:** `https://api.openai.com/v1/images/generations`
- **Models:** `dall-e-3`, `dall-e-2`, `gpt-image-2-medium` (beta)
- **Auth:** `Authorization: Bearer *** **Img2img:** ❌ NOT SUPPORTED. OpenAI API does not do img2img. Only text-to-image.
- **Cost:** $0.04-0.08 per image
- **Caveat:** `401` usually means the key is a ChatGPT web key, not a Platform API key. Must create key at https://platform.openai.com/api-keys

### Pollinations.ai (free, but limited)
- **API:** `https://image.pollinations.ai/prompt/<prompt>` (GET) or POST
- **Cost:** FREE
- **Img2img:** ❌ NOT RELIABLE. Accepts `image` parameter but often ignores it and generates from prompt only.
- **Speed:** 5-15 seconds
- **Caveat:** Good for quick text-to-image tests, not for img2img.

### Stability AI
- **API:** `https://api.stability.ai/v2beta/stable-image/generate/sd3` or `/image-to-image`
- **Auth:** `Authorization: Bearer *** **Img2img:** Supported natively
- **Cost:** ~$0.025-0.08 per image
- **Caveat:** Requires separate Stability API key.

## Local Processing (Pillow)

When AI generation is unavailable, use Pillow for text overlays on existing images.

### Instagram Stories Text Overlay
```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Load image
img = Image.open("photo.jpg").convert('RGBA')
width, height = img.size

# Font (use heavy/bold for Instagram look)
font = ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Heavy.ttf", 90)

# Gradient text + glow effect
# See references/instagram-overlay.py for full working example
```

### Key techniques
- **Glow:** Create separate overlay layer, draw text with expanding pink/red circles, GaussianBlur, composite
- **Gradient text:** Create text mask, apply vertical color gradient (white → pink), composite with mask
- **Shadow:** Black text offset by 2-3px, blurred, at low opacity
- **Fonts:** Lato Heavy, Montserrat, Bebas Neue — popular in Instagram Stories

## Decision Tree

```
Need img2img?
├── Yes
│   ├── Have FAL balance? → FAL (fastest, best)
│   ├── Have Replicate token? → Replicate (good, free tier)
│   ├── Have Stability token? → Stability AI
│   └── No tokens/balance? → Local Pillow (text only) or Google Colab
└── No (text-to-image only)
    ├── Have OpenAI key? → DALL-E 3 (best quality)
    ├── Free? → Pollinations.ai or FAL free tier
    └── Local? → ComfyUI / Stable Diffusion
```

## Common Pitfalls

1. **FAL `403 User is locked`**: Balance exhausted. Need to top up at https://fal.ai/dashboard/billing
2. **OpenAI `401`**: Key is from ChatGPT web, not OpenAI Platform API. Keys must start with `sk-...` from platform.openai.com
3. **Replicate `401 Unauthenticated`**: Token invalid or expired. Regenerate at https://replicate.com/account/api-tokens
4. **Pollinations ignores reference**: The `image` parameter is unreliable for img2img. Use for text-to-image only.
5. **Hermes `image_generate` tool**: Only does text-to-image. For img2img, must use provider API directly via curl/Python.

## References
- `references/instagram-overlay.py` — Working Pillow script for Instagram-style text overlays with glow and gradient
- `references/provider-api-snippets.md` — Copy-paste API snippets for each provider
