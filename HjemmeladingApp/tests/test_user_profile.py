import json
from HjemmeladingApp.modules import user_profile


def test_save_and_load(tmp_path, monkeypatch):
    profile_file = tmp_path / "profile.json"
    # ensure module uses our temp path
    monkeypatch.setattr(user_profile, "PROFILE_PATH", str(profile_file))

    up = user_profile.UserProfile()
    up.data["username"] = "alice"
    up.data["theme"] = "Dark"
    up.save()

    # Create a fresh instance which will load from PROFILE_PATH
    up2 = user_profile.UserProfile()
    assert up2.data["username"] == "alice"
    assert up2.data["theme"] == "Dark"


def test_export_import(tmp_path, monkeypatch):
    profile_file = tmp_path / "profile.json"
    monkeypatch.setattr(user_profile, "PROFILE_PATH", str(profile_file))

    up = user_profile.UserProfile()
    up.data["username"] = "bob"
    up.data["other_settings"] = {"a": 1}
    up.save()

    export_path = tmp_path / "export.json"
    ok = up.export(str(export_path))
    assert ok
    # read exported file
    with open(export_path, "r", encoding="utf-8") as f:
        j = json.load(f)
    assert j["username"] == "bob"

    # modify exported file and import
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump({"username": "charlie"}, f)

    ok2 = up.import_profile(str(export_path))
    assert ok2
    assert up.data["username"] == "charlie"
