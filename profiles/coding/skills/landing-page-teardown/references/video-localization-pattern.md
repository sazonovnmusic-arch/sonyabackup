# Pattern: Localizing Lander Video from Embed to Native Player

## Context
CPA landing pages frequently use externally-hosted or script-injected video players. Affiliates often replace these with a local `<video>` file to reduce dependencies and maintain overlay/tracker control.

## Technique
1. Replace the embed container (e.g., `<div class="embedpvideo" data-videoid="...">`) with a wrapper containing the native `<video>` element and CPA overlays (`#play`, `#open-video`).
2. Port the behavioral JS from the reference lander:
   - Overlay click → `video.muted = false; video.play(); hideOverlays();`
   - `play` event → start a conversion timer (e.g., 180s).
   - `ended` event → show order form (`setEndVideo()`).
   - `pause` event → clear timer.
3. Choose playback UX:
   - **Inline**: Video stays in document flow. Simplest; no scroll-lock or fixed positioning needed.
   - **Fullscreen overlay**: Wrap video in `position: fixed` container, lock body scroll (`overflow: hidden`), add a close button. More immersive but intrusive.
4. Ensure `playsinline` attribute for iOS Safari autoplay/unmute policies.
5. Keep fallback timer (`pageLoadTimer`) so the form shows even if the visitor never clicks the video.

## Pitfalls
- Browser autoplay policies require starting `muted`. Unmute only on first user gesture (overlay click).
- Users expect the complete modified file (e.g., full `index.html`), not patches.
