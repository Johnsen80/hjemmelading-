"""
Init-fil for UI-pakken

Keep this file minimal to avoid importing heavy submodules at package import
time. Importing UI submodules (like `main_window`) may fail during PyInstaller
analysis due to load-order differences; importing them lazily from the code
that needs them is more robust.
"""

__all__ = []
