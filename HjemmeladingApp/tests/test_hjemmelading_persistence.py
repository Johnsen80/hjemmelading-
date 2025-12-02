import pytest

from modules.hjemmelading.storage import load_profile, save_profile


def test_save_and_load_profile(tmp_path):
    data = {"name": "demo", "powder": {"density": 0.95}, "notes": "øæå"}
    p = tmp_path / "profiles" / "demo.json"
    save_profile(data, p)
    loaded = load_profile(p)
    assert loaded == data


def test_load_missing_raises(tmp_path):
    p = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        load_profile(p)


def test_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{ not: valid json }", encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile(p)
