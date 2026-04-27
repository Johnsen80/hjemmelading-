from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from src.database import import_csv, import_grtload

TEST_TMP_ROOT = Path(__file__).resolve().parents[1] / ".github" / "test_tmp"


class _FakeQuery:
    def all(self):
        return []


class _FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False

    def query(self, _model):
        return _FakeQuery()

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.committed = True


@contextmanager
def _local_temp_dir():
    path = TEST_TMP_ROOT / f"import-data-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_import_powder_csv_accepts_flexible_headers():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "powders.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Name,Manufacturer,Burn Rate,Recommended Charge Min,Recommended Charge Max",
                    'N140,Vihtavuori,"12,5","40,0","44,5"',
                ]
            ),
            encoding="utf-8",
        )

        session = _FakeSession()
        errors = import_csv.import_powder_csv(str(csv_path), session, strict=True)

    assert errors == []
    assert session.committed is True
    assert len(session.added) == 1
    powder = session.added[0]
    assert powder.name == "N140"
    assert powder.burn_rate == 12.5
    assert powder.recommended_charge_min == 40.0
    assert powder.recommended_charge_max == 44.5


def test_import_bullet_csv_accepts_header_spacing_and_underscores():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "bullets.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Name,Manufacturer,Diameter,Weight,Recommended_Twist,BC",
                    'ELD-M,Hornady,"7,82","168,0","10,0","0,523"',
                ]
            ),
            encoding="utf-8",
        )

        session = _FakeSession()
        errors = import_csv.import_bullet_csv(str(csv_path), session, strict=True)

    assert errors == []
    assert session.committed is True
    assert len(session.added) == 1
    bullet = session.added[0]
    assert bullet.name == "ELD-M"
    assert bullet.diameter == 7.82
    assert bullet.weight == 168.0
    assert bullet.recommended_twist == 10.0
    assert bullet.bc == 0.523


def test_import_grtload_xml_reports_invalid_charge_range():
    with _local_temp_dir() as tmp_path:
        xml_path = tmp_path / "powders.grtload"
        xml_path.write_text(
            """
<Root>
  <Powder>
    <Name>N150</Name>
    <Manufacturer>Vihtavuori</Manufacturer>
    <BurnRate>15.2</BurnRate>
    <RecommendedChargeMin>46.0</RecommendedChargeMin>
    <RecommendedChargeMax>44.0</RecommendedChargeMax>
  </Powder>
</Root>
            """.strip(),
            encoding="utf-8",
        )

        session = _FakeSession()
        errors = import_grtload.import_grtload_xml(str(xml_path), session, strict=False)

    assert len(errors) == 1
    assert "RecommendedChargeMin cannot exceed RecommendedChargeMax" in errors[0]
    assert session.added == []
    assert session.committed is True


def test_import_powder_csv_accepts_name_aliases_with_units():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "powders_alias.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Powder Name,Brand,Burn Rate Index,Recommended Charge Min (gr),Recommended Charge Max (gr)",
                    "N550,Vihtavuori,18.2,45.0,49.0",
                ]
            ),
            encoding="utf-8",
        )

        session = _FakeSession()
        errors = import_csv.import_powder_csv(str(csv_path), session, strict=True)

    assert errors == []
    powder = session.added[0]
    assert powder.name == "N550"
    assert powder.manufacturer == "Vihtavuori"
    assert powder.burn_rate == 18.2
    assert powder.recommended_charge_min == 45.0
    assert powder.recommended_charge_max == 49.0


def test_import_bullet_csv_accepts_common_unit_aliases():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "bullets_alias.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "Bullet Name,Maker,Diameter (mm),Weight (gr),BC G1,Length (mm),Recommended Twist (in)",
                    "Scenar-L,Lapua,7.82,175.0,0.508,34.2,10.0",
                ]
            ),
            encoding="utf-8",
        )

        session = _FakeSession()
        errors = import_csv.import_bullet_csv(str(csv_path), session, strict=True)

    assert errors == []
    bullet = session.added[0]
    assert bullet.name == "Scenar-L"
    assert bullet.manufacturer == "Lapua"
    assert bullet.diameter == 7.82
    assert bullet.weight == 175.0
    assert bullet.bc == 0.508
    assert bullet.length == 34.2
    assert bullet.recommended_twist == 10.0


def test_build_import_report_counts_duplicates_separately():
    report = import_csv.build_import_report(
        3,
        [
            "Row 4: duplicate powder 'N140' skipped",
            "Row 5: Weight must be a number, got 'abc'",
        ],
    )

    assert report["imported"] == 3
    assert report["duplicates"] == 1
    assert report["validation_errors"] == 1
    assert report["total_errors"] == 2


def test_format_import_report_includes_summary_line():
    lines = import_csv.format_import_report(
        "sample.csv",
        2,
        [
            "Row 3: duplicate powder 'N150' skipped",
            "Row 4: Name is required",
        ],
    )

    assert "2 rader" in lines[0]
    assert "1 duplikater" in lines[0]
    assert "1 valideringsfeil" in lines[0]
    assert "Row 3" in lines[1]


def test_powder_csv_export_import_roundtrip():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "powder_roundtrip.csv"
        rows = [
            SimpleNamespace(
                name="N160",
                manufacturer="Vihtavuori",
                type="Extruded",
                burn_rate=22.4,
                energy_density=3850.0,
                recommended_charge_min=47.0,
                recommended_charge_max=51.0,
                reference="Manual",
            )
        ]
        import_csv.export_powder_csv(str(csv_path), rows)
        exported_text = csv_path.read_text(encoding="utf-8")

        session = _FakeSession()
        errors = import_csv.import_powder_csv(str(csv_path), session, strict=True)

    assert errors == []
    assert "Export Schema Version" in exported_text.splitlines()[0]
    powder = session.added[0]
    assert powder.name == "N160"
    assert powder.manufacturer == "Vihtavuori"
    assert powder.burn_rate == 22.4
    assert powder.recommended_charge_max == 51.0


def test_bullet_csv_export_import_roundtrip():
    with _local_temp_dir() as tmp_path:
        csv_path = tmp_path / "bullet_roundtrip.csv"
        rows = [
            SimpleNamespace(
                name="Hybrid Target",
                manufacturer="Berger",
                diameter=6.71,
                weight=140.0,
                bc=0.618,
                type="Hybrid",
                length=36.3,
                recommended_twist=8.0,
                reference="Catalog",
            )
        ]
        import_csv.export_bullet_csv(str(csv_path), rows)
        exported_text = csv_path.read_text(encoding="utf-8")

        session = _FakeSession()
        errors = import_csv.import_bullet_csv(str(csv_path), session, strict=True)

    assert errors == []
    assert "Export Schema Version" in exported_text.splitlines()[0]
    bullet = session.added[0]
    assert bullet.name == "Hybrid Target"
    assert bullet.manufacturer == "Berger"
    assert bullet.diameter == 6.71
    assert bullet.weight == 140.0
    assert bullet.bc == 0.618
    assert bullet.recommended_twist == 8.0
