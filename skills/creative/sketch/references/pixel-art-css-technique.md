# CSS Box-Shadow Pixel Art Technique

## Technique

Build pixel sprites without images using `box-shadow` on a 4px×4px element. Each shadow offset = one pixel.

```css
.pixel-body {
  position: absolute;
  width: 4px; height: 4px;
  background: transparent;
  box-shadow:
    /* row 0: head top */
    8px 0 0 #3b82f6, 12px 0 0 #3b82f6, 16px 0 0 #3b82f6, 20px 0 0 #3b82f6,
    /* row 1: head sides + face */
    8px 4px 0 #3b82f6, 12px 4px 0 #60a5fa, 16px 4px 0 #60a5fa, 20px 4px 0 #3b82f6,
    /* row 2: head bottom */
    8px 8px 0 #3b82f6, 12px 8px 0 #1e40af, 16px 8px 0 #1e40af, 20px 8px 0 #3b82f6,
    /* row 3: head chin */
    8px 12px 0 #3b82f6, 12px 12px 0 #60a5fa, 16px 12px 0 #60a5fa, 20px 12px 0 #3b82f6,
    /* eyes */
    10px 6px 0 #000, 18px 6px 0 #000,
    /* body row 0 */
    4px 16px 0 #1e3a8a, 8px 16px 0 #2563eb, 12px 16px 0 #2563eb,
    16px 16px 0 #2563eb, 20px 16px 0 #2563eb, 24px 16px 0 #1e3a8a,
    /* body row 1 */
    4px 20px 0 #1e3a8a, 8px 20px 0 #3b82f6, 12px 20px 0 #3b82f6,
    16px 20px 0 #3b82f6, 20px 20px 0 #3b82f6, 24px 20px 0 #1e3a8a,
    /* body row 2: belt/collar */
    4px 24px 0 #1e3a8a, 8px 24px 0 #3b82f6, 12px 24px 0 #fbbf24,
    16px 24px 0 #fbbf24, 20px 24px 0 #3b82f6, 24px 24px 0 #1e3a8a,
    /* body row 3 */
    4px 28px 0 #1e3a8a, 8px 28px 0 #3b82f6, 12px 28px 0 #3b82f6,
    16px 28px 0 #3b82f6, 20px 28px 0 #3b82f6, 24px 28px 0 #1e3a8a,
    /* legs */
    8px 32px 0 #1e3a8a, 12px 32px 0 #1e3a8a, 16px 32px 0 #1e3a8a, 20px 32px 0 #1e3a8a,
    8px 36px 0 #1e3a8a, 20px 36px 0 #1e3a8a;
}
```

## Sizing Guide

| Element | Pixel size | CSS box-shadow count |
|---------|-----------|---------------------|
| Head | 8×8 | ~16 shadows |
| Body | 12×16 | ~24 shadows |
| Full character | ~28×40 | ~40-50 shadows |
| Scene background | 200×120 | Simple divs, not pixels |

## Color Palettes (by agent role)

| Role | Primary | Dark (outline/shadow) | Light (highlight) |
|------|---------|----------------------|-------------------|
| Default / Leader | `#3b82f6` | `#1e3a8a` | `#60a5fa` |
| Coding | `#7c3aed` | `#4c1d95` | `#a78bfa` |
| YouTube | `#dc2626` | `#7f1d1d` | `#f87171` |
| Traffic | `#ea580c` | `#9a3412` | `#fb923c` |
| Instamodel / SMM | `#ec4899` | `#9d174d` | `#f9a8d4` |

## Scene Layout Template

```
┌──────────────────────────────────────┐
│  [Whiteboard]          [Window]      │
│                                      │
│    🧠Default      💻Coding           │
│    [Desk]         [Desk]             │
│                                      │
│    🎬YouTube  📸Instamodel  📢Traffic│
│    [Desk]     [Desk]        [Desk]   │
│                                      │
│  🪴                              ☕   │
└──────────────────────────────────────┘
```

## HTML Structure

```html
<div class="office-scene">
  <!-- Background elements -->
  <div class="floor"></div>
  <div class="window"></div>
  <div class="whiteboard"></div>
  <div class="plant"></div>
  <div class="coffee"></div>

  <!-- Desks (simple divs) -->
  <div class="desk desk-1"></div>
  ...

  <!-- Characters (clickable) -->
  <div class="pixel-char char-default" onclick="openChat('default')">
    <div class="pixel-body"></div>
    <div class="char-label">Default</div>
  </div>
  ...
</div>
```

## Animation

```css
.pixel-char.idle {
  animation: idleMove 2s infinite ease-in-out;
}
@keyframes idleMove {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
```

## Copy-Paste Ready: 5 Agent Sprites

See `templates/pixel-agents.html` for full copy-paste ready sprites with all 5 color variants.
