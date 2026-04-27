import os
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session

from .database import PowderData
from .import_csv import _parse_float, _require_text, format_import_report


def _powder_key(name: str, manufacturer: str | None) -> tuple[str, str]:
    return (name.strip().lower(), (manufacturer or "").strip().lower())


def import_grtload_xml(
    file_path: str,
    db_session: Session,
    strict: bool = True,
    dedupe: bool = True,
) -> list[str]:
    """
    Importer kruttdata fra GRT .grtload XML-fil til PowderData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    tree = ET.parse(file_path)
    root = tree.getroot()
    errors: list[str] = []
    imported = 0

    existing_keys: set[tuple[str, str]] = set()
    if dedupe:
        try:
            existing_keys = {
                _powder_key(row.name or "", row.manufacturer)
                for row in db_session.query(PowderData).all()
            }
        except Exception:
            existing_keys = set()
    seen_keys: set[tuple[str, str]] = set()

    for row_num, powder in enumerate(root.findall(".//Powder"), start=1):
        try:
            name = _require_text(powder.findtext("Name"), "Name", row_num)
            manufacturer = (powder.findtext("Manufacturer") or "").strip() or None
            type_ = (powder.findtext("Type") or "").strip() or None
            burn_rate = _parse_float(
                powder.findtext("BurnRate"),
                "BurnRate",
                row_num,
                min_value=0.0,
                max_value=1000.0,
            )
            energy_density = _parse_float(
                powder.findtext("EnergyDensity"),
                "EnergyDensity",
                row_num,
                min_value=0.0,
                max_value=10000.0,
            )
            charge_min = _parse_float(
                powder.findtext("RecommendedChargeMin"),
                "RecommendedChargeMin",
                row_num,
                min_value=0.0,
                max_value=500.0,
            )
            charge_max = _parse_float(
                powder.findtext("RecommendedChargeMax"),
                "RecommendedChargeMax",
                row_num,
                min_value=0.0,
                max_value=500.0,
            )
            if (
                charge_min is not None
                and charge_max is not None
                and charge_min > charge_max
            ):
                raise ValueError(
                    f"Row {row_num}: RecommendedChargeMin cannot exceed RecommendedChargeMax"
                )
            reference = (powder.findtext("Reference") or "").strip() or None

            key = _powder_key(name, manufacturer)
            if dedupe and (key in existing_keys or key in seen_keys):
                errors.append(f"Row {row_num}: duplicate powder '{name}' skipped")
                continue
            seen_keys.add(key)

            db_powder = PowderData(
                name=name,
                manufacturer=manufacturer,
                type=type_,
                burn_rate=burn_rate,
                energy_density=energy_density,
                recommended_charge_min=charge_min,
                recommended_charge_max=charge_max,
                reference=reference,
            )
            db_session.add(db_powder)
            imported += 1
        except ValueError as exc:
            if strict:
                raise
            errors.append(str(exc))
            continue
        except Exception as exc:
            if strict:
                raise
            errors.append(str(exc))
            continue

    db_session.commit()
    for line in format_import_report(file_path, imported, errors):
        print(line)
    return errors


# Eksempel på bruk:
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# engine = create_engine('sqlite:///hjemmelading.db')
# Session = sessionmaker(bind=engine)
# session = Session()
# import_grtload_xml('POWDER-MEASURE-TEMPLATE.grtload', session)
