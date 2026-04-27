from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/tools/build_saami_coverage_gap_report.py"
    )
    spec = spec_from_file_location("build_saami_coverage_gap_report", script_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_saami_coverage_gap_report_has_counts_and_known_overlap():
    module = _load_module()
    report = module.build_report()

    assert report["counts"]["reference_calibers"] >= 1
    assert report["counts"]["covered_by_saami_seed"] >= 1
    assert "6.5 Creedmoor" in report["covered"]
