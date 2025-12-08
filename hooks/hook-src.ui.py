from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules of the src.ui package so PyInstaller bundles them.
hiddenimports = collect_submodules("src.ui")
