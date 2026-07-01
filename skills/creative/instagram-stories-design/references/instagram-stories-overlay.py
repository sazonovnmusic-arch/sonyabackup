from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_stories_overlay(photo_path, text_main, text_secondary, output_path):
    """
    Накладывает Instagram Stories-style текст на фото.
    Белый→розовый градиент, hot pink glow, чёрная тень.
    """
    img = Image.open(photo_path).convert('RGBA')
    width, height = img.size

    # Find font
    font_candidates = [
        "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
        "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    font_path = None
    for f in font_candidates:
        if os.path.exists(f):
            font_path = f
            break

    if not font_path:
        raise FileNotFoundError("No suitable TTF font found. Install fonts-lato or fonts-dejavu.")

    font_large = ImageFont.truetype(font_path, 95)
    font_small = ImageFont.truetype(font_path, 65)

    # Glow layer
    glow = Image.new('RGBA', img.size, (0,0,0,0))
    glow_draw = ImageDraw.Draw(glow)

    # Measure text
    bbox1 = glow_draw.textbbox((0,0), text_main, font=font_large)
    bbox2 = glow_draw.textbbox((0,0), text_secondary, font=font_small)
    tw1, th1 = bbox1[2]-bbox1[0], bbox1[3]-bbox1[1]
    tw2, th2 = bbox2[2]-bbox2[0], bbox2[3]-bbox2[1]

    x1 = (width - tw1) // 2
    x2 = (width - tw2) // 2
    y1 = height // 5
    y2 = height - height // 4

    # Draw glow (hot pink)
    for r in range(25, 0, -1):
        alpha = int(140 * (1 - r/25))
        color = (255, 20, 147, alpha)
        for dx in range(-r, r+1, 2):
            for dy in range(-r, r+1, 2):
                if dx*dx + dy*dy <= r*r:
                    glow_draw.text((x1+dx, y1+dy), text_main, font=font_large, fill=color)
                    glow_draw.text((x2+dx, y2+dy), text_secondary, font=font_small, fill=color)

    glow = glow.filter(ImageFilter.GaussianBlur(radius=3))

    # Shadow layer
    shadow = Image.new('RGBA', img.size, (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text((x1+3, y1+3), text_main, font=font_large, fill=(0,0,0,120))
    shadow_draw.text((x2+3, y2+3), text_secondary, font=font_small, fill=(0,0,0,120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))

    # Gradient text function
    def gradient_text(text, font, w, h, c1, c2):
        txt = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(txt)
        draw.text((0,0), text, font=font, fill=(255,255,255,255))
        grad = Image.new('RGBA', (w, h))
        for y in range(h):
            ratio = y / h
            r = int(c1[0]*(1-ratio) + c2[0]*ratio)
            g = int(c1[1]*(1-ratio) + c2[1]*ratio)
            b = int(c1[2]*(1-ratio) + c2[2]*ratio)
            for x in range(w):
                grad.putpixel((x,y), (r,g,b,255))
        mask = txt.convert('L')
        return Image.composite(grad, Image.new('RGBA', (w,h), (0,0,0,0)), mask)

    white = (255, 255, 255)
    pink = (255, 105, 180)
    t1_img = gradient_text(text_main, font_large, tw1, th1, white, pink)
    t2_img = gradient_text(text_secondary, font_small, tw2, th2, white, pink)

    # Composite
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, shadow)
    img.paste(t1_img, (x1, y1), t1_img)
    img.paste(t2_img, (x2, y2), t2_img)

    img.convert('RGB').save(output_path, quality=95)
    return output_path


# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python instagram-stories-overlay.py <input.jpg> <output.png> 'Wanna chat?' 'Link in bio'")
        sys.exit(1)
    create_stories_overlay(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
