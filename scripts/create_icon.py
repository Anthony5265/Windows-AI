#!/usr/bin/env python3
"""
Simple icon generator for Windows AI application
Creates a basic icon with "W" text on a gradient background
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(output_path, size=256):
    """Create a simple icon with gradient background and text"""

    # Create image with gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a gradient circle background (blue theme)
    for i in range(size):
        for j in range(size):
            # Calculate distance from center
            dx = i - size/2
            dy = j - size/2
            dist = (dx*dx + dy*dy) ** 0.5

            if dist < size/2:
                # Create gradient from center to edge
                ratio = dist / (size/2)
                r = int(30 + 70 * ratio)
                g = int(100 + 100 * ratio)
                b = int(200 + 55 * ratio)
                a = 255
                img.putpixel((i, j), (r, g, b, a))

    # Draw a "W" in the center
    # Use default font since we may not have access to custom fonts
    try:
        # Try to use a nice font if available
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw text
    text = "W"

    # For newer Pillow versions, use textbbox
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        # Fallback for older versions
        text_width, text_height = draw.textsize(text, font=font)

    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 20

    # Draw white outline
    outline_width = 3
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx*dx + dy*dy <= outline_width*outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=(255, 255, 255, 255))

    # Draw main text in lighter blue
    draw.text((x, y), text, font=font, fill=(220, 240, 255, 255))

    return img

def main():
    """Generate icon in multiple sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    # Create icon directory
    icon_dir = os.path.join(repo_root, 'apps', 'gui', 'renderer')
    os.makedirs(icon_dir, exist_ok=True)

    # Generate 256x256 PNG for Linux/general use
    print("Generating icon.png (256x256)...")
    icon = create_icon(icon_dir, 256)
    icon.save(os.path.join(icon_dir, 'icon.png'), 'PNG')

    # Generate ICO file for Windows with multiple sizes
    print("Generating icon.ico (multi-size)...")
    sizes = [256, 128, 64, 48, 32, 16]
    icons = [create_icon(icon_dir, size) for size in sizes]
    icons[0].save(
        os.path.join(icon_dir, 'icon.ico'),
        format='ICO',
        sizes=[(size, size) for size in sizes]
    )

    # Also save to build directory for installer
    build_dir = os.path.join(repo_root, 'apps', 'gui', 'build')
    os.makedirs(build_dir, exist_ok=True)
    icon.save(os.path.join(build_dir, 'icon.png'), 'PNG')
    icons[0].save(
        os.path.join(build_dir, 'icon.ico'),
        format='ICO',
        sizes=[(size, size) for size in sizes]
    )

    print("Icons created successfully!")
    print(f"  - {os.path.join(icon_dir, 'icon.png')}")
    print(f"  - {os.path.join(icon_dir, 'icon.ico')}")
    print(f"  - {os.path.join(build_dir, 'icon.png')}")
    print(f"  - {os.path.join(build_dir, 'icon.ico')}")

if __name__ == '__main__':
    main()
