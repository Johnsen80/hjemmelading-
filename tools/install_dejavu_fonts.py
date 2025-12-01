"""Download and install DejaVu TTF fonts into the project resources.

This script downloads a DejaVu TTF zip (if available), extracts all .ttf
files into `HjemmeladingApp/resources/fonts/`, and prints a summary.

Run from the project root with the venv Python:
    .\.venv\Scripts\python.exe tools\install_dejavu_fonts.py
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import urllib.request
import tempfile
import zipfile

DEFAULT_URLS = [
    # SourceForge redirect (reliable for releases)
    "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip/download",
    # A GitHub latest-release fallback (may 404 if asset name differs)
    "https://github.com/dejavu-fonts/dejavu-fonts/releases/latest/download/dejavu-fonts-ttf.zip",
]


def ensure_fonts_dir() -> Path:
    p = Path(__file__).resolve().parent.parent / "HjemmeladingApp" / "resources" / "fonts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_and_extract(url: str, dest: Path) -> int:
    print(f"Trying to download fonts from: {url}")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        urllib.request.urlretrieve(url, tmp_path)
    except Exception as e:
        print(f"Download failed: {e}")
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return 0

    added = 0
    try:
        with zipfile.ZipFile(tmp_path, 'r') as z:
            for name in z.namelist():
                if name.lower().endswith('.ttf'):
                    # Extract to dest keeping only filename
                    target = dest / Path(name).name
                    try:
                        with z.open(name) as src, open(target, 'wb') as out:
                            out.write(src.read())
                        added += 1
                    except Exception as e:
                        print(f"Failed to extract {name}: {e}")
    except zipfile.BadZipFile:
        print("Downloaded file is not a zip or is corrupted")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    return added


def main() -> int:
    fonts_dir = ensure_fonts_dir()
    total_added = 0
    for url in DEFAULT_URLS:
        added = download_and_extract(url, fonts_dir)
        if added:
            total_added += added
            break

    if total_added:
        print(f"Added {total_added} .ttf files to {fonts_dir}")
        return 0
    else:
        print("Failed to download/extract DejaVu fonts from known URLs.")
        print("You can manually download DejaVu TTFs and place them in:")
        print(f"  {fonts_dir}")
        return 2


if __name__ == '__main__':
    sys.exit(main())
