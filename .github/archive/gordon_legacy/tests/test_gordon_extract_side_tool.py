from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module(path: Path, name: str):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_analyze_extraction_options_builds_report():
    path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tools/gordon_extract/analyze_extraction_options.py"
    )
    module = _load_module(path, "analyze_extraction_options")
    report = module.build_report()

    assert "paths" in report
    assert report["paths"]["readable_exports"]["status"] == "available"
    assert report["recommended_order"][0] == "readable_exports"


def test_build_plugin_probe_writes_manifest_and_script():
    path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tools/gordon_extract/build_plugin_probe.py"
    )
    module = _load_module(path, "build_plugin_probe")

    output_root = module.OUTPUT_ROOT
    if output_root.exists():
        for child in output_root.iterdir():
            child.unlink()
    else:
        output_root.mkdir(parents=True, exist_ok=True)

    result = module.main()
    assert result == 0
    assert (output_root / "com.grt.plugin.xml").exists()
    assert (output_root / "plugin.py").exists()
    assert (output_root / "plugin.cmd").exists()
    assert (output_root / "README.md").exists()


def test_plugin_probe_attempt_report_builds():
    path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tools/gordon_extract/build_plugin_probe_attempt_report.py"
    )
    module = _load_module(path, "build_plugin_probe_attempt_report")
    report = module.build_report()

    assert "conclusion" in report
    assert "next_recommendation" in report


def test_ui_export_scaffold_builder_writes_files():
    path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tools/gordon_extract/build_ui_export_scaffold.py"
    )
    module = _load_module(path, "build_ui_export_scaffold")
    result = module.main()
    assert result == 0
    assert (module.OUT_DIR / "gordon_ui_export_scaffold.ps1").exists()
    assert (module.OUT_DIR / "gordon_ui_export_scaffold_README.md").exists()
