# Instagram Story Fonts — Best Practices

## Popular fonts in Instagram Stories (as of 2024–2025)

| Font | Style | Use case |
|------|-------|----------|
| **Montserrat Bold/ExtraBold** | Geometric sans-serif | Headlines, CTAs |
| **Bebas Neue** | Tall condensed | Titles, single words |
| **Oswald Bold** | Condensed sans-serif | Uppercase headlines |
| **Playfair Display** | Serif | Luxury/elegant accounts |
| **Inter** | Modern sans-serif | Body text, captions |
| **Poppins** | Rounded sans-serif | Friendly, casual |

## Download sources

- Google Fonts: https://fonts.google.com
  - Direct download via `https://fonts.google.com/download?family=Font+Name`
- GitHub (Montserrat): https://github.com/JulietaUla/Montserrat

## Note on Instagram native fonts

Instagram uses proprietary fonts (Instagram Sans, Instagram Sans Condensed, Instagram Sans Script). These are not available for download. For closest match:
- **Instagram Sans** → Montserrat or Inter
- **Instagram Sans Condensed** → Bebas Neue or Oswald
- **Instagram Sans Script** → Dancing Script or Pacifico (Google Fonts)

## Installation path on this server

All fonts should be placed in `/root/insta_fonts/` and referenced from `FONT_DIR` constant in `insta_story_generator.py`.
