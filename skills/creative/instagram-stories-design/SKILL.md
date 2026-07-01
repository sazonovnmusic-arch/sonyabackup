---
name: instagram-stories-design
description: Overlay Instagram Stories-style text on photos using Pillow with glow, gradient, and shadow effects. Includes known pitfalls for OpenAI image API limitations.
title: Instagram Stories Text Overlay Design
triggers:
  - instagram story
  - stories текст
  - наложить текст на фото
  - wanna chat link in bio
  - story overlay
  - instagram сторис
  - текст на фото инстаграм
  - add text to photo for instagram
---

# Instagram Stories Text Overlay Design

Наложение текста на фото в стиле Instagram Stories. Белый текст с розовым glow, gradient, тени — без использования сторонних UI.

## When to use this skill

- Пользователь просит "сделать stories", "наложить текст на фото", стиль "Wanna chat? / Link in bio"
- Нужно фото + текст в стиле Instagram/Snapchat/TikTok Stories
- Локальная обработка фото (Pillow), без внешних API для редактирования

## Key technique: Pillow overlay with glow + gradient

OpenAI Images API **не поддерживает img2img / редактирование существующих фото**. Только text-to-image. Поэтому для наложения текста на готовое фото используем **Pillow (PIL)** локально.

### Шрифты

Предпочтительные системные шрифты (bold/heavy для stories):
- `Lato-Heavy.ttf` / `Lato-Bold.ttf` — современный, clean
- `DejaVuSans-Bold.ttf` — fallback
- `LiberationSans-Bold.ttf` — fallback

Размеры (для фото ~720x1280):
- Главный текст: **90-95px**
- Вторичный текст: **60-65px**

### Стиль текста (Instagram Stories aesthetic)

```
Цвет: белый → розовый градиент (сверху вниз)
Glow: Hot Pink #FF1493 или #FF69B4, radius 15-25px, alpha 80-140
Shadow: чёрный с blur radius 2, opacity 120/255
Позиция: верхняя треть и нижняя четверть фото, centered
```

### Пример кода

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter

img = Image.open(photo_path).convert('RGBA')
font = ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Heavy.ttf", 95)

# 1. Glow layer (hot pink)
glow = Image.new('RGBA', img.size, (0,0,0,0))
draw = ImageDraw.Draw(glow)
for r in range(25, 0, -1):
    alpha = int(140 * (1 - r/25))
    color = (255, 20, 147, alpha)
    for dx in range(-r, r+1, 2):
        for dy in range(-r, r+1, 2):
            if dx*dx + dy*dy <= r*r:
                draw.text((x+dx, y+dy), text, font=font, fill=color)
glow = glow.filter(ImageFilter.GaussianBlur(radius=3))

# 2. Shadow layer
shadow = Image.new('RGBA', img.size, (0,0,0,0))
draw = ImageDraw.Draw(shadow)
draw.text((x+3, y+3), text, font=font, fill=(0,0,0,120))
shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))

# 3. Gradient text (white → pink)
# Создать текстовую маску, наложить вертикальный градиент

# 4. Composite: img → glow → shadow → text
img = Image.alpha_composite(img, glow)
img = Image.alpha_composite(img, shadow)
# paste gradient text
```

## Pitfalls

1. **OpenAI API ≠ ChatGPT web img2img**: Веб-версия ChatGPT умеет редактировать фото. OpenAI Platform API (`images/generations`) — **только генерация с нуля**. Нельзя подать `reference` или `image` для редактирования.
2. **Токен `sk-proj-...`**: Часто это токен ChatGPT (веб), а не OpenAI Platform API. Для API нужен ключ с https://platform.openai.com/api-keys.
3. **Шрифты**: На minimal Linux-контейнерах может не быть TTF. Проверять `find /usr/share/fonts -name "*.ttf"`. Lato — обычно есть.
4. **Pillow default font**: `ImageFont.load_default()` — ужасный bitmap, не использовать для stories.

## References

- `references/instagram-stories-overlay.py` — полный рабочий скрипт overlay
