from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

"""
Instagram Stories text overlay script.
Creates white-to-pink gradient text with soft glow effect.
Requires: Pillow (pip install Pillow)
Fonts: Lato Heavy (system package fonts-lato) or similar bold sans-serif
"""

def create_instagram_overlay(image_path, text_lines, output_path, 
                              font_path="/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
                              font_sizes=(90, 65),
                              colors=((255, 255, 255), (255, 105, 180)),
                              glow_color=(255, 20, 147, 140),
                              glow_radius=25):
    """
    Add Instagram-style text overlay to an image.
    
    Args:
        image_path: Path to source image
        text_lines: List of strings to overlay (e.g., ["Wanna chat?", "Link in bio"])
        output_path: Where to save result
        font_path: Path to TTF font file (heavy/bold for Instagram look)
        font_sizes: Tuple of (main_size, secondary_size)
        colors: Tuple of (top_color, bottom_color) for gradient (RGB tuples)
        glow_color: RGBA tuple for glow color
        glow_radius: Pixel radius for glow effect
    """
    img = Image.open(image_path).convert('RGBA')
    width, height = img.size
    
    font_large = ImageFont.truetype(font_path, font_sizes[0])
    font_small = ImageFont.truetype(font_path, font_sizes[1])
    fonts = [font_large, font_small]
    
    # Create glow overlay
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Positions
    positions = []
    y_positions = [height // 5, height - height // 4]
    
    for i, text in enumerate(text_lines):
        bbox = glow_draw.textbbox((0, 0), text, font=fonts[i])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (width - tw) // 2
        y = y_positions[i]
        positions.append((x, y, tw, th))
        
        # Draw glow
        for r in range(glow_radius, 0, -1):
            alpha = int(glow_color[3] * (1 - r/glow_radius))
            color = (*glow_color[:3], alpha)
            for dx in range(-r, r + 1, 2):
                for dy in range(-r, r + 1, 2):
                    if dx * dx + dy * dy <= r * r:
                        glow_draw.text((x + dx, y + dy), text, font=fonts[i], fill=color)
    
    # Blur glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Gradient text function
    def gradient_text(text, font, w, h, color1, color2):
        txt = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt)
        draw.text((0, 0), text, font=font, fill=(255, 255, 255, 255))
        
        grad = Image.new('RGBA', (w, h))
        for y in range(h):
            ratio = y / h
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            for x in range(w):
                grad.putpixel((x, y), (r, g, b, 255))
        
        txt_mask = txt.convert('L')
        result = Image.composite(grad, Image.new('RGBA', (w, h), (0, 0, 0, 0)), txt_mask)
        return result
    
    # Shadow layer
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    for i, text in enumerate(text_lines):
        x, y, tw, th = positions[i]
        shadow_draw.text((x + 3, y + 3), text, font=fonts[i], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Composite
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, shadow)
    
    for i, text in enumerate(text_lines):
        x, y, tw, th = positions[i]
        text_img = gradient_text(text, fonts[i], tw, th, colors[0], colors[1])
        img.paste(text_img, (x, y), text_img)
    
    img.convert('RGB').save(output_path, quality=95)
    print(f"Saved: {output_path}")


# Example usage
if __name__ == "__main__":
    create_instagram_overlay(
        image_path="/path/to/photo.jpg",
        text_lines=["Wanna chat?", "Link in bio"],
        output_path="/path/to/output.png"
    )
