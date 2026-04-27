from pathlib import Path

from src.modules import component_database as component_module


def test_resolve_gordon_extract_paths_reports_required_files():
    tmp_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_paths_missing_case_a"
    )
    tmp_path.mkdir(parents=True, exist_ok=True)

    resolved = component_module.resolve_gordon_extract_paths(tmp_path)

    assert resolved["extract_dir"] == tmp_path
    assert resolved["projectiles"] == tmp_path / "full_projectiles.xml"
    assert resolved["propellants"] == tmp_path / "full_propellants.xml"
    assert resolved["calibers"] is None
    assert len(resolved["required_missing"]) == 2


def test_resolve_gordon_extract_paths_accepts_optional_caliber_file():
    tmp_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_paths_present_case_a"
    )
    tmp_path.mkdir(parents=True, exist_ok=True)

    projectiles = tmp_path / "gordon_extracted_projectiles_raw.csv"
    propellants = tmp_path / "gordon_extracted_propellants_raw.csv"
    calibers = tmp_path / "gordon_extracted_calibers_raw.csv"
    projectiles.write_text("col\nvalue\n", encoding="utf-8")
    propellants.write_text("col\nvalue\n", encoding="utf-8")
    calibers.write_text("col\nvalue\n", encoding="utf-8")

    resolved = component_module.resolve_gordon_extract_paths(tmp_path)

    assert resolved["required_missing"] == []
    assert resolved["calibers"] == calibers


def test_resolve_gordon_extract_paths_prefers_full_xml_exports():
    tmp_path = Path(
        "c:/Users/bjjoh/OneDrive/Dokumenter/Programering/Hjemmelading/.github/test_tmp/gordon_paths_full_xml_case_a"
    )
    tmp_path.mkdir(parents=True, exist_ok=True)

    projectiles = tmp_path / "full_projectiles.xml"
    propellants = tmp_path / "full_propellants.xml"
    calibers = tmp_path / "full_calibers.xml"
    projectiles.write_text("<GordonsReloadingTool />", encoding="utf-8")
    propellants.write_text("<GordonsReloadingTool />", encoding="utf-8")
    calibers.write_text("<GordonsReloadingTool />", encoding="utf-8")

    resolved = component_module.resolve_gordon_extract_paths(tmp_path)

    assert resolved["projectiles"] == projectiles
    assert resolved["propellants"] == propellants
    assert resolved["calibers"] == calibers
    assert resolved["required_missing"] == []
