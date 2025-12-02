from HjemmeladingApp.utils import safe_logger


def test_append_message_and_exception(tmp_path, monkeypatch):
    # Force LOCALAPPDATA to our tmp path so logger writes there
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    safe_logger.append_message("hello world", app_name="TestApp")
    log_path = safe_logger.get_debug_log_path("TestApp")
    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "hello world" in content

    try:
        raise ValueError("bad value")
    except Exception as exc:
        safe_logger.append_exception("an error occurred", exc=exc, app_name="TestApp")

    content2 = log_path.read_text(encoding="utf-8")
    assert "ValueError" in content2 or "bad value" in content2
