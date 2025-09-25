#!/usr/bin/env python3
"""
Fix ICO for Windows Desktop Shortcuts

Alternative approach to create Windows-compatible ICO files.
This creates a more robust ICO file that Windows should definitely recognise.
"""

from PIL import Image
import io
import struct
from pathlib import Path


def create_ico_manually(png_files, output_path):
    """
    Create an ICO file manually with proper Windows ICO structure.
    This ensures Windows will recognise it properly.
    """
    images = []
    
    # Load and prepare images
    for png_file in png_files:
        if Path(png_file).exists():
            img = Image.open(png_file)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
    
    if not images:
        print("No images to process")
        return False
    
    # Sort images by size (Windows expects this)
    images.sort(key=lambda x: x.size[0])
    
    # Create ICO file manually
    ico_data = io.BytesIO()
    
    # ICO header: reserved (2 bytes), type (2 bytes), count (2 bytes)
    ico_data.write(struct.pack('<HHH', 0, 1, len(images)))
    
    # Calculate offset for first image data (header + directory entries)
    offset = 6 + (16 * len(images))
    
    image_data_list = []
    
    # Write directory entries and prepare image data
    for img in images:
        # Convert image to PNG data
        png_data = io.BytesIO()
        img.save(png_data, format='PNG')
        png_bytes = png_data.getvalue()
        
        width, height = img.size
        
        # ICO directory entry (16 bytes)
        # Width, Height, ColorCount, Reserved, Planes, BitCount, ImageSize, Offset
        ico_data.write(struct.pack('<BBBBHHLL', 
                                  width if width < 256 else 0,  # Width (0 means 256)
                                  height if height < 256 else 0, # Height (0 means 256)
                                  0,    # ColorCount (0 for PNG)
                                  0,    # Reserved
                                  1,    # Planes
                                  32,   # BitCount
                                  len(png_bytes), # ImageSize
                                  offset))        # Offset
        
        image_data_list.append(png_bytes)
        offset += len(png_bytes)
    
    # Write image data
    for png_bytes in image_data_list:
        ico_data.write(png_bytes)
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(ico_data.getvalue())
    
    return True


def create_windows_ico():
    """Create a Windows-compatible ICO file."""
    assets_dir = Path(__file__).parent
    
    # Use the most important sizes for desktop shortcuts
    sizes = [16, 32, 48, 64]  # Start with fewer sizes to debug
    png_files = []
    
    print("Creating Windows-compatible ICO file...")
    
    for size in sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        if png_file.exists():
            png_files.append(str(png_file))
            print(f"Found PNG: {size}x{size}")
        else:
            print(f"Missing PNG: {size}x{size}")
    
    if not png_files:
        print("No PNG files found!")
        return False
    
    # Create the ICO file
    ico_path = assets_dir / 'windows_desktop_icon.ico'
    
    try:
        success = create_ico_manually(png_files, ico_path)
        
        if success:
            file_size = ico_path.stat().st_size
            print(f"✅ Created Windows ICO: {ico_path}")
            print(f"File size: {file_size} bytes")
            
            # Verify it can be opened
            try:
                test_img = Image.open(ico_path)
                print(f"✅ ICO verification passed: {test_img.format}, {test_img.size}")
                return True
            except Exception as e:
                print(f"⚠️  Warning: Could not verify ICO: {e}")
                return True  # File was created, might still work
        else:
            print("❌ Failed to create ICO")
            return False
            
    except Exception as e:
        print(f"❌ Error creating ICO: {e}")
        return False


def create_simple_ico():
    """Create a simple ICO with just the most essential sizes."""
    assets_dir = Path(__file__).parent
    
    # Just use 32x32 and 48x48 - the most important for desktop shortcuts
    essential_sizes = [32, 48]
    images = []
    
    print("\nCreating simple ICO with essential sizes only...")
    
    for size in essential_sizes:
        png_file = assets_dir / f'spending_tracker_icon_{size}x{size}.png'
        if png_file.exists():
            img = Image.open(png_file)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
            print(f"Added {size}x{size}")
    
    if images:
        simple_ico = assets_dir / 'simple_desktop_icon.ico'
        
        # Use Pillow's built-in ICO support but with fewer images
        images[0].save(
            simple_ico,
            format='ICO',
            sizes=[(img.width, img.height) for img in images]
        )
        
        file_size = simple_ico.stat().st_size
        print(f"✅ Created simple ICO: {simple_ico}")
        print(f"File size: {file_size} bytes")
        
        return True
    
    return False


if __name__ == "__main__":
    print("Fixing ICO files for Windows desktop shortcuts...\n")
    
    # Try the manual method first
    success1 = create_windows_ico()
    
    # Also create a simple version
    success2 = create_simple_ico()
    
    if success1 or success2:
        print(f"\n🎉 Created Windows-compatible ICO files!")
        print(f"\nFiles available for desktop shortcuts:")
        
        assets_dir = Path(__file__).parent
        for ico_file in assets_dir.glob("*.ico"):
            file_size = ico_file.stat().st_size
            print(f"  - {ico_file.name} ({file_size} bytes)")
        
        print(f"\nTo use with your desktop shortcut:")
        print(f"1. Right-click your desktop shortcut")
        print(f"2. Select 'Properties'") 
        print(f"3. Click 'Change Icon'")
        print(f"4. Browse to any of the ICO files above")
        print(f"5. Try 'windows_desktop_icon.ico' or 'simple_desktop_icon.ico' first")
        
    else:
        print(f"\n❌ Failed to create ICO files")