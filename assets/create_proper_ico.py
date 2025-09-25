#!/usr/bin/env python3
"""
Create Proper ICO File for Windows Desktop Shortcuts

This script creates a proper multi-size ICO file that Windows will recognise
for desktop shortcuts and system integration.
"""

from PIL import Image
import os
from pathlib import Path


def create_proper_ico():
    """Create a properly formatted ICO file with multiple sizes."""
    assets_dir = Path(__file__).parent
    
    # Define the sizes we need for a proper Windows ICO
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    print("Creating proper ICO file for Windows desktop shortcuts...")
    
    # Load each PNG size and add to images list
    for size in sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        
        if png_file.exists():
            img = Image.open(png_file)
            # Ensure the image is in RGBA mode for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
            print(f"Added {size}x{size} icon to ICO")
        else:
            print(f"Warning: {png_file} not found, skipping {size}x{size}")
    
    if not images:
        print("Error: No PNG files found to create ICO")
        return False
    
    # Create the ICO file with all sizes
    ico_path = assets_dir / 'spending_tracker_icon.ico'
    
    # Save with proper ICO format - this method creates a multi-size ICO
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:] if len(images) > 1 else []
    )
    
    print(f"✅ Created proper ICO file: {ico_path}")
    
    # Verify the ICO file
    try:
        test_img = Image.open(ico_path)
        print(f"ICO verification: Format={test_img.format}, Size={test_img.size}")
        
        # Check file size to ensure it's not empty
        file_size = os.path.getsize(ico_path)
        print(f"ICO file size: {file_size} bytes")
        
        if file_size < 1000:  # Less than 1KB is suspicious
            print("⚠️  Warning: ICO file seems small, may not contain all sizes")
        else:
            print("✅ ICO file looks good!")
            
    except Exception as e:
        print(f"Error verifying ICO file: {e}")
        return False
    
    return True


def create_desktop_shortcut_ico():
    """Create an ICO specifically optimised for desktop shortcuts."""
    assets_dir = Path(__file__).parent
    
    # For desktop shortcuts, we primarily need 32x32 and 48x48
    # but including more sizes for compatibility
    priority_sizes = [32, 48, 16, 64, 128]
    images = []
    
    print("\nCreating desktop shortcut optimised ICO...")
    
    for size in priority_sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        
        if png_file.exists():
            img = Image.open(png_file)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
            print(f"Added {size}x{size} for desktop shortcut")
    
    if images:
        shortcut_ico = assets_dir / 'desktop_shortcut_icon.ico'
        images[0].save(
            shortcut_ico,
            format='ICO',
            sizes=[(img.width, img.height) for img in images],
            append_images=images[1:] if len(images) > 1 else []
        )
        
        print(f"✅ Created desktop shortcut ICO: {shortcut_ico}")
        
        # Verify
        file_size = os.path.getsize(shortcut_ico)
        print(f"Desktop ICO file size: {file_size} bytes")
        
        return True
    
    return False


if __name__ == "__main__":
    success1 = create_proper_ico()
    success2 = create_desktop_shortcut_ico()
    
    if success1 or success2:
        print("\n🎉 ICO files created successfully!")
        print("\nTo use with your desktop shortcut:")
        print("1. Right-click your desktop shortcut")
        print("2. Select 'Properties'")
        print("3. Click 'Change Icon'")
        print("4. Browse to: spending_tracker_icon.ico or desktop_shortcut_icon.ico")
        print("5. Select the icon and click OK")
    else:
        print("\n❌ Failed to create ICO files")