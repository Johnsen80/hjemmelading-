from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

EXPECTED_FILENAMES = ("projectile.xml", "propellant.xml", "caliber.xml")
DEFAULT_APPDATA_ROOT = Path(os.getenv("APPDATA", "")) / "GordonsReloadingTool"
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "tmp" / "gordon_user_files"


def collect_gordon_user_files(
    source_root: Path,
    output_root: Path,
) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)

    copied_files: list[dict[str, object]] = []
    missing_files: list[str] = []

    for filename in EXPECTED_FILENAMES:
        source_path = source_root / filename
        if not source_path.exists():
            missing_files.append(filename)
            continue

        destination_path = output_root / filename
        shutil.copy2(source_path, destination_path)
        copied_files.append(
            {
                "name": filename,
                "source": str(source_path),
                "destination": str(destination_path),
                "size_bytes": source_path.stat().st_size,
            }
        )

    summary = {
        "source_root": str(source_root),
        "output_root": str(output_root),
        "expected_files": list(EXPECTED_FILENAMES),
        "copied_count": len(copied_files),
        "missing_count": len(missing_files),
        "copied_files": copied_files,
        "missing_files": missing_files,
    }

    summary_path = output_root / "gordon_user_files_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect Gordon user XML files from AppData into a local ingest folder."
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_APPDATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    summary = collect_gordon_user_files(args.source_root, args.output_root)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
