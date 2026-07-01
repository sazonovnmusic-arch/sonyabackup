# img2img Provider Testing Notes

Session: June 24, 2026 — testing various img2img providers for Instagram Story generation.

## Tested Providers

### FAL.ai ⭐ Best quality
- **Endpoint:** `https://fal.run/fal-ai/flux-redux`
- **Model:** FLUX.1 Redux (img2img)
- **Price:** ~$0.02–0.08 per image
- **Result:** Account locked immediately — "Exhausted balance"
- **Note:** Requires prepaid balance. Fastest (1–2s), best quality.

### Replicate
- **Endpoint:** `https://api.replicate.com/v1/predictions`
- **Models:** FLUX, SDXL
- **Free tier:** $5 on signup
- **Result:** Multiple tokens tested, all returned `401 Unauthenticated`
- **Note:** User likely provided ChatGPT tokens, not Replicate API tokens.

### Pollinations.ai
- **Endpoint:** `https://image.pollinations.ai/prompt`
- **Price:** Free
- **Result:** Returns 200 OK but **ignores reference image entirely**. Generates abstract art.
- **Note:** NOT suitable for img2img.

### OpenAI Images API
- **Endpoint:** `https://api.openai.com/v1/images/generations`
- **Result:** `reference` parameter rejected. No native img2img support.
- **Note:** DALL-E is text-to-image only.

## Conclusion

For Instagram Stories with text overlays, **local Pillow generation is superior** to any API:
- Zero cost, instant, full control, no tokens.
