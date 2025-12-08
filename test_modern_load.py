"""
Test modern_load_builder import
"""

import traceback

try:
    print("Testing import...")
    from src.modules.modern_load_builder import ModernLoadBuilder

    print("✅ Import successful!")

    print("\nTesting class instantiation...")
    builder = ModernLoadBuilder()
    print("✅ Class created successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
