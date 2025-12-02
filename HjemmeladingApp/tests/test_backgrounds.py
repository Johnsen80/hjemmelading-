import os
from HjemmeladingApp.utils import backgrounds


def test_validate_and_save_background(tmp_path, monkeypatch):
    # Force LOCALAPPDATA to our tmp path so backgrounds dir is created there
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    # create a small dummy file with .png extension
    img_path = tmp_path / "small.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)

    ok, kind = backgrounds.validate_image(str(img_path))
    assert ok
    assert kind in ("png", "jpeg", "gif", "bmp")

    saved = backgrounds.save_background(str(img_path))
    assert os.path.exists(saved)
