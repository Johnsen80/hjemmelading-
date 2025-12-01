"""
Generate desktop icon (.ico) for HJEMMELADING
Creates multi-resolution icon file for Windows desktop shortcut
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
import sys
import os

def generate_desktop_icon():
    """Generate .ico file with multiple resolutions"""
    app = QApplication(sys.argv)
    
    # Import tactical logo
    from src.assets.logo_tactical import CompactTacticalIcon
    
    # Standard Windows icon sizes
    sizes = [256, 128, 64, 48, 32, 16]
    
    # Create QIcon with multiple resolutions
    icon = QIcon()
    
    for size in sizes:
        # Create widget
        widget = CompactTacticalIcon(size)
        
        # Render to pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        widget.render(painter)
        painter.end()
        
        # Add to icon
        icon.addPixmap(pixmap)
        
        print(f"✓ Generated {size}x{size} icon")
    
    # Save as .ico file
    icon_path = os.path.join(os.path.dirname(__file__), "hjemmelading.ico")
    pixmap_256 = icon.pixmap(QSize(256, 256))
    pixmap_256.save(icon_path, "ICO")
    
    print(f"\n✅ Icon saved to: {icon_path}")
    print(f"📁 Full path: {os.path.abspath(icon_path)}")
    
    return icon_path


if __name__ == '__main__':
    print("🎯 HJEMMELADING - Desktop Icon Generator")
    print("=" * 50)
    
    icon_path = generate_desktop_icon()
    
    print("\n" + "=" * 50)
    print("✅ DONE! Desktop icon created!")
    print("\n📌 To create desktop shortcut:")
    print("1. Right-click on desktop → New → Shortcut")
    print(f"2. Location: python [full path to main.py]")
    print(f"3. Name: HJEMMELADING")
    print(f"4. Right-click shortcut → Properties → Change Icon")
    print(f"5. Browse to: {os.path.abspath(icon_path)}")
    print("\n🚀 Your tactical reloading system is ready!")
