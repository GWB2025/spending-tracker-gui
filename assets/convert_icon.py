#!/usr/bin/env python3
"""
Icon Conversion Script for Spending Tracker GUI

This script converts the SVG icon to various formats needed for the application:
- Windows ICO format for the application icon
- PNG formats in various sizes
"""

import cairosvg
from PIL import Image
import io
import os
from pathlib import Path


def svg_to_png(svg_path, output_path, width, height):
    """Convert SVG to PNG with specified dimensions."""
    png_data = cairosvg.svg2png(
        file_open=open(svg_path, 'rb'),
        output_width=width,
        output_height=height
    )
    
    with open(output_path, 'wb') as f:
        f.write(png_data)
    
    print(f"Created PNG: {output_path} ({width}x{height})")


def create_ico_from_svg(svg_path, ico_path, sizes=None):
    """Create ICO file from SVG with multiple sizes."""
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    images = []
    
    for size in sizes:
        # Convert SVG to PNG data in memory
        png_data = cairosvg.svg2png(
            file_open=open(svg_path, 'rb'),
            output_width=size,
            output_height=size
        )
        
        # Create PIL Image from PNG data
        img = Image.open(io.BytesIO(png_data))
        images.append(img)
        print(f"Generated {size}x{size} icon layer")
    
    # Save all sizes as ICO
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images]
    )
    
    print(f"Created ICO file: {ico_path}")


def main():
    """Main conversion process."""
    # Set up paths
    assets_dir = Path(__file__).parent
    svg_file = assets_dir / 'spending_tracker_icon.svg'
    
    if not svg_file.exists():
        print(f"Error: SVG file not found at {svg_file}")
        return
    
    print(f"Converting icon from: {svg_file}")
    
    # Create ICO file for Windows
    ico_file = assets_dir / 'spending_tracker_icon.ico'
    create_ico_from_svg(str(svg_file), str(ico_file))
    
    # Create PNG files in various sizes
    png_sizes = [16, 32, 48, 64, 128, 256]
    
    for size in png_sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        svg_to_png(str(svg_file), str(png_file), size, size)
    
    # Create app icon (256x256 for high DPI displays)
    app_icon = assets_dir / 'app_icon.png'
    svg_to_png(str(svg_file), str(app_icon), 256, 256)
    
    print("\n✅ Icon conversion complete!")
    print(f"Files created in: {assets_dir}")
    print("\nFiles generated:")
    print("- spending_tracker_icon.ico (Windows application icon)")
    print("- spending_tracker_icon_*.png (Various sizes)")
    print("- app_icon.png (High-res application icon)")


if __name__ == "__main__":
    main()