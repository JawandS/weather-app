"""Generate rainbow weather app icons"""
from PIL import Image, ImageDraw
import math

def create_rainbow_weather_icon(size):
    """Create a beautiful rainbow weather icon at the specified size"""
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    s = size / 512
    
    # Background gradient (dark blue)
    for y in range(size):
        for x in range(size):
            # Check if pixel is within circle
            dist = math.sqrt((x - size/2)**2 + (y - size/2)**2)
            if dist <= size/2:
                # Gradient from top-left to bottom-right
                t = (x + y) / (2 * size)
                r = int(26 + t * (15 - 26))
                g = int(26 + t * (52 - 26))
                b = int(46 + t * (96 - 46))
                img.putpixel((x, y), (r, g, b, 255))
    
    # Rainbow colors
    rainbow_colors = [
        (255, 107, 107),  # Red
        (255, 230, 109),  # Yellow
        (78, 205, 196),   # Teal
        (69, 183, 209),   # Blue
        (150, 201, 61),   # Green
    ]
    
    # Draw rainbow arcs (background decoration)
    center_x = size // 2
    arc_y = int(340 * s)
    
    # Background rainbow arc (subtle)
    for i, color in enumerate(rainbow_colors):
        arc_size = int((300 - i * 25) * s)
        arc_width = int(8 * s)
        bbox = [
            center_x - arc_size,
            arc_y - arc_size,
            center_x + arc_size,
            arc_y + arc_size
        ]
        r, g, b = color
        draw.arc(bbox, 180, 360, fill=(r, g, b, 60), width=arc_width)
    
    # Sun parameters
    sun_x = int(256 * s)
    sun_y = int(180 * s)
    sun_radius = int(50 * s)
    glow_radius = int(70 * s)
    
    # Sun glow
    for r in range(glow_radius, sun_radius, -2):
        alpha = int(255 * (1 - (r - sun_radius) / (glow_radius - sun_radius)) * 0.5)
        color = (255, 200, 100, alpha)
        draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=color)
    
    # Main sun
    draw.ellipse([sun_x - sun_radius, sun_y - sun_radius, 
                  sun_x + sun_radius, sun_y + sun_radius], 
                 fill=(255, 230, 109, 255))
    
    # Sun rays
    ray_color = (255, 230, 109, 200)
    ray_length = int(20 * s)
    ray_width = int(6 * s)
    ray_start = sun_radius + int(10 * s)
    
    angles = [0, 45, 90, 135, 180, 225, 270, 315]
    for angle in angles:
        rad = math.radians(angle)
        x1 = sun_x + int(ray_start * math.cos(rad))
        y1 = sun_y + int(ray_start * math.sin(rad))
        x2 = sun_x + int((ray_start + ray_length) * math.cos(rad))
        y2 = sun_y + int((ray_start + ray_length) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=ray_color, width=ray_width)
    
    # Cloud shape (multiple overlapping ellipses)
    cloud_color = (255, 255, 255, 245)
    cloud_parts = [
        (200, 320, 70, 50),
        (280, 310, 80, 55),
        (340, 330, 60, 45),
        (150, 340, 50, 35),
        (240, 350, 100, 40),
    ]
    
    for cx, cy, rx, ry in cloud_parts:
        cx, cy, rx, ry = int(cx * s), int(cy * s), int(rx * s), int(ry * s)
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=cloud_color)
    
    # Rainbow stripes on cloud
    stripe_data = [
        (140, 355, 200, 6),
        (150, 365, 180, 6),
        (160, 375, 160, 6),
        (170, 385, 140, 6),
        (180, 395, 120, 6),
    ]
    
    for i, (x, y, w, h) in enumerate(stripe_data):
        x, y, w, h = int(x * s), int(y * s), int(w * s), int(h * s)
        r, g, b = rainbow_colors[i]
        # Draw rounded rectangle (using rounded corners)
        radius = h // 2
        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=(r, g, b, 180))
    
    # Sparkle accents
    sparkles = [(380, 120, 4), (420, 180, 3), (100, 150, 3), (130, 200, 4)]
    for sx, sy, sr in sparkles:
        sx, sy, sr = int(sx * s), int(sy * s), int(sr * s)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 255, 255, 230))
    
    # Apply circular mask for clean edges
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size, size], fill=255)
    
    # Create final image with mask
    final = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    final.paste(img, (0, 0), mask)
    
    return final


def main():
    # Generate icons in required sizes
    sizes = [180, 192, 512]
    
    for size in sizes:
        print(f"Generating {size}x{size} icon...")
        icon = create_rainbow_weather_icon(size)
        icon.save(f'/home/js/projects/weather-app/static/icons/icon-{size}.png', 'PNG')
        print(f"Saved icon-{size}.png")
    
    # Also create a 32x32 favicon
    print("Generating 32x32 favicon...")
    favicon = create_rainbow_weather_icon(32)
    favicon.save('/home/js/projects/weather-app/static/icons/favicon-32.png', 'PNG')
    
    # Create ICO file with multiple sizes
    print("Generating favicon.ico...")
    icon_16 = create_rainbow_weather_icon(16)
    icon_32 = create_rainbow_weather_icon(32)
    icon_48 = create_rainbow_weather_icon(48)
    icon_16.save('/home/js/projects/weather-app/static/icons/favicon.ico', format='ICO', 
                 sizes=[(16, 16), (32, 32), (48, 48)],
                 append_images=[icon_32, icon_48])
    
    print("All icons generated successfully!")


if __name__ == '__main__':
    main()
