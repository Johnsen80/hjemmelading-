from __future__ import annotations

import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY\plugins\hjemmelading_gordon_probe"
)
NESTED_PLUGIN_ROOT = PLUGIN_ROOT / "gordon_plugin_probe"
LOG_PATH = PLUGIN_ROOT / "probe_log.jsonl"
PLUGIN_CMD = PLUGIN_ROOT / "plugin.cmd"
TOP_MANIFEST = PLUGIN_ROOT / "com.grt.plugin.xml"


def read_plugin_enabled(xml_path: Path) -> str | None:
    if not xml_path.exists():
        return None
    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    plugin = root.find("plugin")
    if plugin is None:
        return None
    return plugin.attrib.get("enabled")


def read_manifest_attributes(xml_path: Path) -> dict[str, str]:
    if not xml_path.exists():
        return {}
    root = ET.fromstring(xml_path.read_text(encoding="utf-8"))
    plugin = root.find("plugin")
    if plugin is None:
        return {}
    return dict(plugin.attrib)


def resolve_launch_target() -> Path | None:
    attrs = read_manifest_attributes(TOP_MANIFEST)
    launch_windows = attrs.get("launch-windows")
    if not launch_windows:
        return None
    path = Path(launch_windows)
    if path.is_absolute():
        return path
    return PLUGIN_ROOT / launch_windows


def tail_jsonl(path: Path, limit: int = 10) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[
        -limit:
    ]:
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"raw": line})
    return rows


def run_plugin_cmd_selftest() -> dict[str, object]:
    before_size = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    result = subprocess.run(
        [str(PLUGIN_CMD)], capture_output=True, text=True, timeout=10, shell=True
    )
    time.sleep(0.5)
    entries = tail_jsonl(LOG_PATH, limit=5)
    after_size = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    startup = next(
        (entry for entry in reversed(entries) if entry.get("event") == "startup"), None
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "log_grew": after_size > before_size,
        "latest_startup": startup,
    }


def run_launch_target_selftest() -> dict[str, object]:
    launch_target = resolve_launch_target()
    if launch_target is None:
        return {"exists": False, "error": "launch-windows missing"}
    if not launch_target.exists():
        return {"exists": False, "path": str(launch_target)}
    before_size = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    result = subprocess.run(
        [str(launch_target)], capture_output=True, text=True, timeout=10
    )
    time.sleep(0.5)
    entries = tail_jsonl(LOG_PATH, limit=5)
    after_size = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
    startup = next(
        (entry for entry in reversed(entries) if entry.get("event") == "startup"), None
    )
    return {
        "exists": True,
        "path": str(launch_target),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "log_grew": after_size > before_size,
        "latest_startup": startup,
    }


def main(argv: list[str]) -> int:
    report = {
        "plugin_root": str(PLUGIN_ROOT),
        "top_manifest": read_manifest_attributes(TOP_MANIFEST),
        "top_manifest_enabled": read_plugin_enabled(PLUGIN_ROOT / "com.grt.plugin.xml"),
        "nested_manifest_enabled": read_plugin_enabled(
            NESTED_PLUGIN_ROOT / "com.grt.plugin.xml"
        ),
        "plugin_cmd_exists": PLUGIN_CMD.exists(),
        "resolved_launch_target": str(resolve_launch_target() or ""),
        "probe_log_exists": LOG_PATH.exists(),
        "recent_log_entries": tail_jsonl(LOG_PATH, limit=8),
        "selftest": run_plugin_cmd_selftest(),
        "launch_target_selftest": run_launch_target_selftest(),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
