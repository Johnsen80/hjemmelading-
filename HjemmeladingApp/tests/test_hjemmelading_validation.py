import pytest

from modules.hjemmelading.validation import validate_profile


def test_validate_profile_accepts_minimal():
    p = {"username": "a"}
    cleaned = validate_profile(p)
    assert cleaned["username"] == "a"
    assert "theme" in cleaned


def test_validate_profile_rejects_non_dict():
    with pytest.raises(ValueError):
        validate_profile("not a dict")


def test_validate_profile_rejects_bad_theme():
    with pytest.raises(ValueError):
        validate_profile({"theme": "unknown-theme"})


def test_validate_profile_handles_extra_keys():
    p = {"username": "bob", "extra": 123}
    cleaned = validate_profile(p)
    assert cleaned.get("extra") == 123


def test_validate_profile_other_settings_must_be_dict():
    with pytest.raises(ValueError):
        validate_profile({"other_settings": "not a dict"})
