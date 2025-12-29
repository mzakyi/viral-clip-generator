"""
Font Helper for MoviePy Text Overlays
Automatically finds and uses available system fonts
"""

import os
import platform
from pathlib import Path

def get_available_font():
    """
    Find an available font on the system that works with MoviePy/Pillow
    Returns the full path to a working font file
    """
    
    system = platform.system()
    
    # Common font paths by operating system
    font_paths = []
    
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
        ]
    
    elif system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/Library/Fonts/Arial.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Verdana.ttf",
            "/Library/Fonts/Verdana Bold.ttf",
        ]
    
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
    
    # Try to find first available font
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"✓ Found font: {font_path}")
            return font_path
    
    # If no font found, return None and MoviePy will use default
    print("⚠ No font found, using MoviePy default")
    return None


def get_font_for_text_overlay(fontsize=50, color='white', bold=True):
    """
    Returns a font configuration dict for MoviePy TextClip
    """
    font_path = get_available_font()
    
    config = {
        'fontsize': fontsize,
        'color': color,
        'stroke_color': 'black',
        'stroke_width': 2,
        'method': 'caption',
    }
    
    # Only add font if we found one
    if font_path:
        config['font'] = font_path
    
    return config


# Test function
if __name__ == "__main__":
    print(f"System: {platform.system()}")
    print(f"Testing font detection...")
    font = get_available_font()
    if font:
        print(f"✓ Font available: {font}")
    else:
        print("✗ No font found, will use default")