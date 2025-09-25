#!/usr/bin/env python3
"""
Simple Icon Conversion Script for Spending Tracker GUI (Windows Compatible)

This script creates PNG icons from a base design and converts them to ICO format
using only Pillow, which is Windows-compatible.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


def create_spending_tracker_icon(size, output_path):
    """Create a spending tracker icon using PIL drawing functions."""
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate scaling factor based on size
    scale = size / 256
    
    # Define colours (British green theme)
    bg_color = (46, 139, 87)  # Sea green
    accent_color = (255, 215, 0)  # Gold
    white = (255, 255, 255)
    dark_green = (31, 95, 63)
    
    # Draw background circle with shadow effect
    shadow_offset = max(1, int(3 * scale))
    shadow_radius = max(1, int(120 * scale))
    main_radius = max(1, int(115 * scale))
    center = size // 2
    
    # Shadow
    draw.ellipse(
        [center - shadow_radius + shadow_offset, 
         center - shadow_radius + shadow_offset, 
         center + shadow_radius + shadow_offset, 
         center + shadow_radius + shadow_offset],
        fill=(0, 0, 0, 50)
    )
    
    # Main background circle
    draw.ellipse(
        [center - main_radius, center - main_radius, 
         center + main_radius, center + main_radius],
        fill=bg_color
    )
    
    # Inner white circle for contrast
    inner_radius = max(1, int(100 * scale))
    draw.ellipse(
        [center - inner_radius, center - inner_radius, 
         center + inner_radius, center + inner_radius],
        fill=white
    )
    
    # Draw pound symbol (£) - simplified version
    pound_size = max(1, int(40 * scale))
    pound_x = center - int(20 * scale)
    pound_y = center - int(30 * scale)
    
    # Pound symbol outline (simplified)
    line_width = max(1, int(4 * scale))
    
    # Vertical line of £
    draw.line(
        [pound_x, pound_y, pound_x, pound_y + pound_size],
        fill=bg_color, width=line_width
    )
    
    # Top curve
    draw.arc(
        [pound_x - int(5 * scale), pound_y, 
         pound_x + int(15 * scale), pound_y + int(20 * scale)],
        start=180, end=0, fill=bg_color, width=line_width
    )
    
    # Horizontal lines
    draw.line(
        [pound_x - int(5 * scale), pound_y + int(15 * scale),
         pound_x + int(15 * scale), pound_y + int(15 * scale)],
        fill=bg_color, width=line_width
    )
    
    draw.line(
        [pound_x - int(5 * scale), pound_y + int(35 * scale),
         pound_x + int(20 * scale), pound_y + int(35 * scale)],
        fill=bg_color, width=line_width
    )
    
    # Draw chart bars (right side)
    chart_x = center + int(10 * scale)
    chart_y = center - int(10 * scale)
    bar_width = max(1, int(8 * scale))
    bar_spacing = max(1, int(12 * scale))
    
    bar_heights = [int(20 * scale), int(35 * scale), int(25 * scale), int(40 * scale)]
    
    for i, height in enumerate(bar_heights):
        x = chart_x + i * bar_spacing
        y = chart_y + (int(40 * scale) - height)
        draw.rectangle(
            [x, y, x + bar_width, chart_y + int(40 * scale)],
            fill=accent_color
        )
    
    # Draw small decorative elements
    coin_radius = max(1, int(6 * scale))
    
    # Small coins
    draw.ellipse(
        [center + int(60 * scale) - coin_radius, center - int(60 * scale) - coin_radius,
         center + int(60 * scale) + coin_radius, center - int(60 * scale) + coin_radius],
        fill=accent_color
    )
    
    draw.ellipse(
        [center + int(70 * scale) - coin_radius//2, center - int(40 * scale) - coin_radius//2,
         center + int(70 * scale) + coin_radius//2, center - int(40 * scale) + coin_radius//2],
        fill=accent_color
    )
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"Created icon: {output_path} ({size}x{size})")


def create_ico_from_pngs(png_files, ico_path):
    """Create ICO file from multiple PNG files."""
    images = []
    
    for png_file in png_files:
        if os.path.exists(png_file):
            img = Image.open(png_file)
            images.append(img)
    
    if images:
        # Save all sizes as ICO
        images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        print(f"Created ICO file: {ico_path}")
    else:
        print("No PNG files found to create ICO")


def main():
    """Main conversion process."""
    # Set up paths
    assets_dir = Path(__file__).parent
    
    print("Creating spending tracker icons...")
    
    # Create PNG files in various sizes
    png_sizes = [16, 32, 48, 64, 128, 256]
    png_files = []
    
    for size in png_sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        png_files.append(str(png_file))
        create_spending_tracker_icon(size, str(png_file))
    
    # Create main app icon
    app_icon = assets_dir / 'app_icon.png'
    create_spending_tracker_icon(256, str(app_icon))
    
    # Create ICO file for Windows
    ico_file = assets_dir / 'spending_tracker_icon.ico'
    create_ico_from_pngs(png_files, str(ico_file))
    
    print("\n✅ Icon creation complete!")
    print(f"Files created in: {assets_dir}")
    print("\nFiles generated:")
    print("- spending_tracker_icon.ico (Windows application icon)")
    print("- spending_tracker_icon_*.png (Various sizes)")
    print("- app_icon.png (High-res application icon)")


if __name__ == "__main__":
    main()