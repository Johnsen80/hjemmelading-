from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TMP_DIR = REPO_ROOT / ".github" / "tmp"
INSTALL_ROOT = Path(
    r"C:\Users\bjjoh\Desktop\GordonsReloadingTool-2021.2030-NIGHTLY\GordonsReloadingTool-2021.2030-NIGHTLY"
)
PLUGIN_ROOT = INSTALL_ROOT / "plugins" / "hjemmelading_gordon_probe"


def build_report() -> dict[str, object]:
    plugin_files = []
    if PLUGIN_ROOT.exists():
        plugin_files = sorted(item.name for item in PLUGIN_ROOT.iterdir())

    probe_logs = (
        sorted(INSTALL_ROOT.rglob("probe_log.jsonl")) if INSTALL_ROOT.exists() else []
    )

    probe_log_found = bool(probe_logs)
    conclusion = (
        "Plugin probe deployed and Gordon launched, but no probe_log.jsonl was produced. "
        "This suggests the plugin process is not being started, or exits before logging."
    )
    if probe_log_found:
        conclusion = (
            "Plugin probe is starting and writing logs. The remaining issue is now the IPC protocol "
            "and response parsing, not plugin startup."
        )

    return {
        "install_root": str(INSTALL_ROOT),
        "plugin_root": str(PLUGIN_ROOT),
        "plugin_root_exists": PLUGIN_ROOT.exists(),
        "plugin_files": plugin_files,
        "probe_log_found": probe_log_found,
        "probe_logs": [str(path) for path in probe_logs],
        "conclusion": conclusion,
        "next_recommendation": [
            "Refine the probe to capture raw IPC payloads and response framing.",
            "Test simpler/known-good commands and Event_Attached parsing before database ambitions.",
            "Fallback to UI automation if plugin-sporet stalls after protocol work.",
            "Keep DB-forensics as last resort.",
        ],
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gordon Plugin Probe Attempt",
        "",
        f"- Install root: `{report['install_root']}`",
        f"- Plugin root: `{report['plugin_root']}`",
        f"- Plugin root exists: `{report['plugin_root_exists']}`",
        "",
        "## Plugin Files",
    ]
    for name in report["plugin_files"]:
        lines.append(f"- `{name}`")
    if not report["plugin_files"]:
        lines.append("- Ingen")

    lines.extend(
        [
            "",
            f"- Probe log found: `{report['probe_log_found']}`",
        ]
    )
    if report["probe_logs"]:
        lines.append("")
        lines.append("## Probe Logs")
        for path in report["probe_logs"]:
            lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## Conclusion",
            f"- {report['conclusion']}",
            "",
            "## Next Recommendation",
        ]
    )
    for item in report["next_recommendation"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    out_dir = TMP_DIR / "gordon_extract"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    json_path = out_dir / "plugin_probe_attempt_report.json"
    md_path = out_dir / "plugin_probe_attempt_report.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(build_markdown(report), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
