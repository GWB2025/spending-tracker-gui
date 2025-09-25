# Spending Tracker GUI - Assets

This directory contains the custom icons and assets for the Spending Tracker GUI application.

## Icon Files

### Main Application Icons

- **`spending_tracker_icon.ico`** - Windows application icon (multi-resolution ICO format)
- **`app_icon.png`** - High-resolution PNG application icon (256×256)
- **`spending_tracker_icon.svg`** - Original scalable vector source file

### PNG Icons (Multiple Sizes)

- `spending_tracker_icon_16x16.png` - Small icon for system tray, favicons
- `spending_tracker_icon_32x32.png` - Medium icon for toolbar buttons
- `spending_tracker_icon_48x48.png` - Standard Windows icon size
- `spending_tracker_icon_64x64.png` - High DPI medium size
- `spending_tracker_icon_128x128.png` - Large icon for high DPI displays
- `spending_tracker_icon_256x256.png` - Extra large icon

## Icon Design

The custom icon features:

### Design Elements
- **Circular background** with British sea green gradient (#2E8B57 to #228B22)
- **Pound sterling symbol (£)** as the primary focal point
- **Chart bars** representing spending data visualisation
- **Ledger/notebook** element symbolising financial record-keeping
- **Gold accents** (#FFD700) for visual appeal and money association
- **Professional colour scheme** suitable for financial applications

### Design Philosophy
- **British styling** - Uses pound sterling symbol and British green colours
- **Financial focus** - Incorporates money, charts, and ledger symbols
- **Professional appearance** - Clean, modern design suitable for desktop applications
- **Scalability** - Vector-based design that works well at all sizes
- **Windows compatibility** - ICO format with multiple resolutions

## Usage in PySide6

### Setting Application Icon

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from pathlib import Path

# Get icon path
assets_dir = Path(__file__).parent.parent / 'assets'
icon_path = str(assets_dir / 'spending_tracker_icon.ico')

# Set application icon
app = QApplication()
app.setWindowIcon(QIcon(icon_path))
```

### Setting Window Icon

```python
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QIcon
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window icon
        assets_dir = Path(__file__).parent.parent / 'assets'
        icon_path = str(assets_dir / 'app_icon.png')
        self.setWindowIcon(QIcon(icon_path))
```

## Generation Scripts

### `simple_convert_icon.py`
Windows-compatible script that generates all icon formats using only Pillow (PIL). This is the recommended script for generating icons on Windows systems.

### `convert_icon.py`
Advanced script that uses CairoSVG for high-quality SVG conversion. Requires Cairo libraries which may not be available on all Windows systems.

### Regenerating Icons

To regenerate all icon formats:

```bash
cd assets
python simple_convert_icon.py
```

## File Structure

```
assets/
├── README.md                           # This documentation
├── spending_tracker_icon.svg           # Original vector source
├── spending_tracker_icon.ico           # Windows application icon
├── app_icon.png                        # Main application icon (256×256)
├── spending_tracker_icon_16x16.png     # Small size
├── spending_tracker_icon_32x32.png     # Medium size  
├── spending_tracker_icon_48x48.png     # Standard size
├── spending_tracker_icon_64x64.png     # High DPI medium
├── spending_tracker_icon_128x128.png   # Large size
├── spending_tracker_icon_256x256.png   # Extra large
├── simple_convert_icon.py              # Icon generation script (Windows)
├── convert_icon.py                     # Advanced generation script
└── icon_integration_example.py         # PySide6 integration examples
```

## Customisation

To modify the icon design:

1. Edit `spending_tracker_icon.svg` in a vector graphics editor (like Inkscape)
2. Run `python simple_convert_icon.py` to regenerate all formats
3. Alternatively, modify the drawing code in `simple_convert_icon.py` for programmatic changes

## Colour Palette

- **Primary Green**: #2E8B57 (Sea Green)
- **Secondary Green**: #228B22 (Forest Green)  
- **Accent Gold**: #FFD700 (Gold)
- **Accent Orange**: #FFA500 (Orange)
- **Dark Green**: #1F5F3F (Dark Sea Green)
- **Background White**: #FFFFFF

All colours chosen to represent financial stability and British design sensibilities.