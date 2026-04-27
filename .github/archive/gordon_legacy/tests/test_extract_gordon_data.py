from __future__ import annotations

import importlib.util
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path


def _load_extract_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / ".github" / "tools" / "extract_gordon_data.py"
    spec = importlib.util.spec_from_file_location(
        "extract_gordon_data_tool", module_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


@contextmanager
def _local_temp_dir():
    path = TEST_TMP_ROOT / f"extract-gordon-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_extract_gordon_data_reads_projectile_propellant_and_caliber_export_xml(
    monkeypatch,
):
    module = _load_extract_module()
    with _local_temp_dir() as tmp_path:
        monkeypatch.setenv("APPDATA", str(tmp_path / "empty_appdata"))

        export_xml = tmp_path / "gordon_export.xml"
        export_xml.write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <projectilefile>
    <var name="mname" value="Lapua" />
    <var name="pname" value="Scenar GB422 7069" />
    <var name="lotid" value="7069" />
    <var name="caliber" value=".308" />
    <var name="gdia" value="7.82" />
    <var name="glen" value="33.20" />
    <var name="gmass" value="167" />
    <var name="gpressure" value="250" />
    <var name="g1bc" value="0.446" />
    <var name="g7bc" value="0.223" />
    <var name="gUBCS" value="T0F1F2C4N1" />
    <var name="type" value="BTHP" />
    <var name="mode" value="userfile" />
  </projectilefile>
  <propellantfile>
    <var name="mname" value="Vihtavuori" />
    <var name="pname" value="N540" />
    <var name="lotid" value="2021-09-30" />
    <var name="Ba" value="0.5728" />
    <var name="Qex" value="4000.0" />
    <var name="k" value="1.2171" />
    <var name="eta" value="972.0" />
    <var name="a0" value="0.0" />
    <var name="z1" value="0.55" />
    <var name="z2" value="0.95" />
    <var name="pc" value="1580.0" />
    <var name="pcd" value="930.0" />
    <var name="pt" value="300.0" />
    <var name="tcc" value="1.0" />
    <var name="tch" value="0.0" />
    <var name="mode" value="userfile" />
  </propellantfile>
  <caliberfile>
    <var name="cipname" value=".308 Winchester" />
    <var name="standard" value="C.I.P." />
    <var name="ciporigin" value="US" />
    <var name="cippdf" value="https://bobp.cip-bobp.org/uploads/tdcc/tab-i/308-win-en.pdf" />
    <var name="L3" value="51.18" />
    <var name="L6" value="71.12" />
    <var name="V" value="3.64" />
    <var name="Pmax" value="4150" />
    <var name="G1" value="7.82" />
  </caliberfile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )

        extracted = module.extract_gordon_data(tmp_path)

        assert len(extracted["raw_projectiles"]) == 1
        assert len(extracted["raw_propellants"]) == 1
        assert len(extracted["raw_calibers"]) == 1

        bullet = extracted["bullets_for_app"][0]
        assert bullet["manufacturer"] == "Lapua"
        assert bullet["name"] == "Scenar GB422 7069"
        assert bullet["caliber"] == ".308"
        assert bullet["weight"] == 167.0
        assert bullet["bc_g1"] == 0.446
        assert bullet["bc_g7"] == 0.223

        powder = extracted["powders_for_app"][0]
        assert powder["manufacturer"] == "Vihtavuori"
        assert powder["name"] == "N540"
        assert powder["density"] == 0.93
        assert powder["burn_rate"] == "0.5728"
        powder_ref = extracted["propellant_reference_rows"][0]
        assert powder_ref["Ba"] == 0.5728
        assert powder_ref["pcd_kg_m3"] == 930.0

        caliber = extracted["calibers_for_reference"][0]
        assert caliber["name"] == ".308 Winchester"
        assert caliber["standard"] == "C.I.P."
        assert caliber["case_length_mm"] == 51.18
        assert caliber["oal_mm"] == 71.12
        assert caliber["case_capacity_ml"] == 3.64
        assert caliber["max_pressure_bar"] == 4150.0
        caliber_ref = extracted["caliber_reference_rows"][0]
        assert caliber_ref["cipname"] == ".308 Winchester"
        assert caliber_ref["L6_oal_mm"] == 71.12

        projectile_ref = extracted["projectile_reference_rows"][0]
        assert projectile_ref["manufacturer"] == "Lapua"
        assert projectile_ref["mass_gr"] == 167.0
        assert projectile_ref["g1_bc"] == 0.446


def test_extract_gordon_data_reads_native_gordon_file_extensions(monkeypatch):
    module = _load_extract_module()
    with _local_temp_dir() as tmp_path:
        monkeypatch.setenv("APPDATA", str(tmp_path / "empty_appdata"))

        (tmp_path / "bullet.projectile").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <projectilefile>
    <var name="mname" value="Lapua" />
    <var name="pname" value="Scenar GB491 7073" />
    <var name="caliber" value=".308" />
    <var name="gdia" value="7.82" />
    <var name="glen" value="35.10" />
    <var name="gmass" value="155.0" />
    <var name="gBC0" value="0.460" />
    <var name="g7bc" value="0.230" />
  </projectilefile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )
        (tmp_path / "powder.propellant").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <propellantfile>
    <var name="mname" value="Vihtavuori" />
    <var name="pname" value="N540" />
    <var name="lotid" value="2021-09-30" />
    <var name="Ba" value="0.5728" />
    <var name="pcd" value="930" />
  </propellantfile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )
        (tmp_path / "caliber.caliber").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <caliberfile>
    <var name="cipname" value=".308%20Win." />
    <var name="standard" value="CIP" />
    <var name="L3" value="51.18" />
    <var name="L6" value="71.12" />
    <var name="Pmax" value="4150.00" />
    <var name="V" value="56.00" />
    <var name="G1" value="7.82" />
  </caliberfile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )

        extracted = module.extract_gordon_data(tmp_path)

        assert len(extracted["raw_projectiles"]) == 1
        assert len(extracted["raw_propellants"]) == 1
        assert len(extracted["raw_calibers"]) == 1
        assert extracted["bullets_for_app"][0]["manufacturer"] == "Lapua"
        assert extracted["powders_for_app"][0]["name"] == "N540"
        assert extracted["calibers_for_reference"][0]["name"] == ".308 Win."


def test_extract_gordon_data_reads_extra_component_roots(monkeypatch):
    module = _load_extract_module()
    with _local_temp_dir() as tmp_path:
        monkeypatch.setenv("APPDATA", str(tmp_path / "empty_appdata"))
        install_root = tmp_path / "install"
        extra_root = tmp_path / "user_files"
        install_root.mkdir(parents=True, exist_ok=True)
        extra_root.mkdir(parents=True, exist_ok=True)

        (extra_root / "projectile.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <projectilefile>
    <var name="mname" value="Hornady" />
    <var name="pname" value="ELD-M 30713" />
    <var name="caliber" value=".308" />
    <var name="gdia" value="7.82" />
    <var name="glen" value="33.80" />
    <var name="gmass" value="168" />
  </projectilefile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )

        extracted = module.extract_gordon_data(
            install_root,
            extra_component_roots=[extra_root],
        )

        assert len(extracted["raw_projectiles"]) == 1
        assert extracted["bullets_for_app"][0]["manufacturer"] == "Hornady"


def test_extract_gordon_data_can_disable_default_appdata(monkeypatch):
    module = _load_extract_module()
    with _local_temp_dir() as tmp_path:
        appdata_root = tmp_path / "appdata"
        (appdata_root / "GordonsReloadingTool").mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("APPDATA", str(appdata_root))

        (appdata_root / "GordonsReloadingTool" / "projectile.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <projectilefile>
    <var name="mname" value="Lapua" />
    <var name="pname" value="Scenar" />
    <var name="caliber" value=".308" />
    <var name="gdia" value="7.82" />
    <var name="glen" value="35.10" />
    <var name="gmass" value="155.0" />
  </projectilefile>
</GordonsReloadingTool>
""",
            encoding="utf-8",
        )
        install_root = tmp_path / "nested" / "install"
        install_root.mkdir(parents=True, exist_ok=True)

        extracted = module.extract_gordon_data(
            install_root,
            include_default_appdata=False,
        )

        assert extracted["raw_projectiles"] == []
