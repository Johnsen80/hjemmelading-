from src.utils import i18n


def test_tr_falls_back_to_other_language_when_key_missing(monkeypatch):
    translator = i18n.Translations()
    monkeypatch.setattr(i18n, "_translator", translator)

    translator.translations["no"]["shared_only_in_no"] = "Bare norsk"
    translator.set_language("en")

    assert i18n.tr("shared_only_in_no") == "Bare norsk"


def test_missing_translation_report_tracks_missing_keys_per_language(monkeypatch):
    translator = i18n.Translations()
    monkeypatch.setattr(i18n, "_translator", translator)
    translator.clear_missing_keys()
    translator.set_language("en")

    assert i18n.tr("totally_missing_key") == "totally_missing_key"

    report = i18n.get_missing_translation_report()

    assert "en" in report
    assert "no" in report
    assert "totally_missing_key" in report["en"]
    assert "totally_missing_key" in report["no"]


def test_clear_missing_translation_report_resets_state(monkeypatch):
    translator = i18n.Translations()
    monkeypatch.setattr(i18n, "_translator", translator)
    translator.set_language("no")
    i18n.tr("another_missing_key")

    i18n.clear_missing_translation_report()

    assert i18n.get_missing_translation_report() == {}
