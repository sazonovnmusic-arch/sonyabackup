---
name: landing-page-teardown
description: Analyze marketing and CPA landing pages (HTML/CSS/JS) to understand their structure, conversion mechanisms, video implementations, tracking, and dark patterns.
category: software-development
tags:
  - landing-page
  - cpa
  - marketing
  - html-analysis
  - conversion
---

# Landing Page Teardown

Analyze landing page source code to map out structure, conversion tactics, and technical implementation.

## Trigger

- User pastes or uploads HTML/JS/CSS from a landing page and asks what's inside, how it works, or how a specific element (video, form, timer, etc.) is implemented.
- User shares a scraped/cloned lander and asks to understand or modify it.

## References
- `references/video-localization-pattern.md` — Replacing embed/video players with native `<video>` + CPA overlays.
- `references/limonad-cpa-form.md` — Full Limonad `./lemon.php` hidden-field stack and migration checklist from generic `order.php`.

## Steps

### 1. Skeleton scan first
Identify major blocks: header/brand bar, hero, video section, order form, fake testimonials/comments, footer.

### 2. Focus on the asked component
If the user specifically asks about video, form, or tracking — deep-dive there. Summarize or skip decorative blocks (fake comments, media logos, long text) without repetitive "this is irrelevant" remarks.

### 3. Map external resources
Note linked stylesheets and scripts by filename. Numbered scripts (`scripts/27.js`, `scripts/28.js`) usually hold the active logic. Ask for the specific JS files early if the behavior isn't inline.

### 4. Identify dark patterns / CPA tricks
- **Scarcity**: fake stock counters, countdown timers, "only X left".
- **Fake social proof**: static HTML tables mimicking Facebook/Instagram comments (randomized `opacity` values like `1.0002`, `1.0166`).
- **Back-button hijacking**: commented-out or active `<script>` blocks manipulating `history.pushState` / `onpopstate` to redirect on back press.
- **Exit-intent / popups**: modals injected dynamically.
- **Tracking pixels**: Facebook Pixel cookies, hidden UTM fields in forms, `save_url.php`-style loggers capturing referrer and `subid`.

### 5. Video player mapping
- Check `<video>` vs iframe (YouTube/Vimeo).
- Attributes: `playsinline` (iOS fullscreen prevention), `muted`, `autoplay`, `preload="metadata"`.
- Overlays: look for sibling `<div>` elements (`#open-video`, `#popup`, `#play`) used as CPA click-traps layered above the player.
- Controls logic: if absent inline, it's likely in one of the numbered JS files.

### 6. Order form mapping
- Hidden fields: affiliate `subid`, `clickid`, `pixel`, `offer_id`, UTM params.
- Price display pattern: crossed-out old price + bold new price with `.oldPriceAndLabelForLandingInfoApi` / `.priceAndLabelForLandingInfoApi` classes.
- Phone validation: often client-side regex with country-specific minimum length checks.

## Pitfalls

- **Chunked pastes**: users often dump an entire page source in multiple messages. Don't interrupt every chunk with "this is irrelevant." Acknowledge once and redirect: *"Вижу ты скидываешь весь файл по частям — давай или всё сразу файлом, или скинь конкретно JS-файлы (scripts/27.js и 28.js) для разбора логики видео."*
- **Commented-out scripts**: CPA landers frequently contain large disabled `<script>` blocks that reveal intended back-button or redirect behavior. Don't ignore them.
- **Fake comments**: these are purely static HTML `<table>` blocks. Their only notable feature is inline opacity randomization to simulate "live" loading. Do not analyze them as functional components.
* **External PHP endpoints**: forms often POST to `lemon.php`, `save_url.php`, etc. Note the endpoints for security review.
* **Modification delivery format**: When the user asks you to *modify* or *rebuild* a lander (not just analyze it), provide complete, copy-paste-ready files (e.g., full `index.html` or `.js`). Avoid splitting deliverables into fragmented snippets. Offer to write the complete file to disk for direct download. Keep prose explanations concise when the code is self-explanatory.

## Verification

Summarize findings in a structured bullet list:
- **Structure**
- **Video / Form logic**
- **Tracking**
- **Dark patterns**
