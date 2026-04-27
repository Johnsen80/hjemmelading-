import csv
import os
import re

from sqlalchemy.orm import Session

from .database import BulletData, PowderData

EXPORT_SCHEMA_VERSION = "component_csv.v1"


HEADER_ALIASES = {
    "powdername": "name",
    "bulletname": "name",
    "projectilename": "name",
    "brand": "manufacturer",
    "maker": "manufacturer",
    "burnrateindex": "burnrate",
    "energydensityjcc": "energydensity",
    "recommendedchargemingr": "recommendedchargemin",
    "recommendedchargemaxgr": "recommendedchargemax",
    "chargeweightmin": "recommendedchargemin",
    "chargeweightmax": "recommendedchargemax",
    "diametermm": "diameter",
    "diameterin": "diameter",
    "weightgr": "weight",
    "bulletweightgr": "weight",
    "projectileweightgr": "weight",
    "bcg1": "bc",
    "bcg7": "bc",
    "lengthmm": "length",
    "recommendedtwistin": "recommendedtwist",
    "recommendedtwistrate": "recommendedtwist",
}


def _normalize_number(value: str) -> str:
    cleaned = value.strip()
    if "," in cleaned and "." not in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and parts[0].replace("-", "").isdigit():
            cleaned = cleaned.replace(",", ".")
    return cleaned


def _normalize_header(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = value.strip().lstrip("\ufeff").lower()
    normalized = re.sub(r"[^a-z0-9]+", "", cleaned)
    return HEADER_ALIASES.get(normalized, normalized)


def _normalize_row(row: dict) -> dict:
    normalized: dict[str, object] = {}
    for key, value in row.items():
        header = _normalize_header(key)
        if not header:
            continue
        normalized[header] = value
    return normalized


def _validate_required_headers(
    fieldnames: list[str] | None,
    required: list[str],
    file_path: str,
    strict: bool,
    errors: list[str],
) -> bool:
    normalized = {_normalize_header(name) for name in (fieldnames or []) if name}
    missing = [name for name in required if name.lower() not in normalized]
    if missing:
        msg = f"Missing required columns in {file_path}: {', '.join(missing)}"
        if strict:
            raise ValueError(msg)
        errors.append(msg)
        return False
    return True


def _powder_key(name: str, manufacturer: str | None) -> tuple[str, str]:
    return (name.strip().lower(), (manufacturer or "").strip().lower())


def _bullet_key(
    name: str,
    manufacturer: str | None,
    weight: float | None,
    diameter: float | None,
) -> tuple[str, str, str, str]:
    return (
        name.strip().lower(),
        (manufacturer or "").strip().lower(),
        "" if weight is None else f"{weight:.4f}",
        "" if diameter is None else f"{diameter:.4f}",
    )


def _require_text(value: str | None, field: str, row_num: int) -> str:
    if value is None:
        raise ValueError(f"Row {row_num}: {field} is required")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"Row {row_num}: {field} is required")
    return cleaned


def _parse_float(
    value: str | None,
    field: str,
    row_num: int,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    raw = _normalize_number(str(value))
    try:
        parsed = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_num}: {field} must be a number, got {value!r}"
        ) from exc

    if min_value is not None and parsed < min_value:
        raise ValueError(f"Row {row_num}: {field} must be >= {min_value}, got {parsed}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"Row {row_num}: {field} must be <= {max_value}, got {parsed}")
    return parsed


def build_import_report(imported: int, errors: list[str]) -> dict[str, int]:
    duplicates = 0
    validation_errors = 0
    for error in errors:
        lower = str(error).lower()
        if "duplicate" in lower and "skipped" in lower:
            duplicates += 1
        else:
            validation_errors += 1
    return {
        "imported": imported,
        "duplicates": duplicates,
        "validation_errors": validation_errors,
        "total_errors": len(errors),
    }


def format_import_report(file_path: str, imported: int, errors: list[str]) -> list[str]:
    report = build_import_report(imported, errors)
    if not errors:
        return [f"Importert data fra {file_path} ({imported} rader)"]
    lines = [
        (
            f"Importert data fra {file_path}: {report['imported']} rader, "
            f"{report['duplicates']} duplikater hoppet over, "
            f"{report['validation_errors']} valideringsfeil"
        )
    ]
    lines.extend(errors[:5])
    return lines


def export_powder_csv(file_path: str, rows: list[object]) -> None:
    fieldnames = [
        "Export Schema Version",
        "Name",
        "Manufacturer",
        "Type",
        "Burn Rate",
        "Energy Density",
        "Recommended Charge Min",
        "Recommended Charge Max",
        "Reference",
    ]
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Export Schema Version": EXPORT_SCHEMA_VERSION,
                    "Name": getattr(row, "name", None),
                    "Manufacturer": getattr(row, "manufacturer", None),
                    "Type": getattr(row, "type", None),
                    "Burn Rate": getattr(row, "burn_rate", None),
                    "Energy Density": getattr(row, "energy_density", None),
                    "Recommended Charge Min": getattr(
                        row, "recommended_charge_min", None
                    ),
                    "Recommended Charge Max": getattr(
                        row, "recommended_charge_max", None
                    ),
                    "Reference": getattr(row, "reference", None),
                }
            )


def export_bullet_csv(file_path: str, rows: list[object]) -> None:
    fieldnames = [
        "Export Schema Version",
        "Name",
        "Manufacturer",
        "Diameter",
        "Weight",
        "BC",
        "Type",
        "Length",
        "Recommended Twist",
        "Reference",
    ]
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Export Schema Version": EXPORT_SCHEMA_VERSION,
                    "Name": getattr(row, "name", None),
                    "Manufacturer": getattr(row, "manufacturer", None),
                    "Diameter": getattr(row, "diameter", None),
                    "Weight": getattr(row, "weight", None),
                    "BC": getattr(row, "bc", None),
                    "Type": getattr(row, "type", None),
                    "Length": getattr(row, "length", None),
                    "Recommended Twist": getattr(row, "recommended_twist", None),
                    "Reference": getattr(row, "reference", None),
                }
            )


def import_powder_csv(
    file_path: str,
    db_session: Session,
    strict: bool = True,
    dedupe: bool = True,
) -> list[str]:
    """
    Importer kruttdata fra CSV-fil til PowderData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    errors: list[str] = []
    imported = 0
    with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        if not _validate_required_headers(
            reader.fieldnames,
            ["Name"],
            file_path,
            strict,
            errors,
        ):
            return errors

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
        for row_num, row in enumerate(reader, start=2):
            try:
                row_norm = _normalize_row(row)
                name = _require_text(row_norm.get("name"), "Name", row_num)
                manufacturer = row_norm.get("manufacturer") or ""
                manufacturer = str(manufacturer).strip() or None
                powder_type = row_norm.get("type") or ""
                powder_type = str(powder_type).strip() or None
                burn_rate = _parse_float(
                    row_norm.get("burnrate"),
                    "BurnRate",
                    row_num,
                    min_value=0.0,
                    max_value=1000.0,
                )
                energy_density = _parse_float(
                    row_norm.get("energydensity"),
                    "EnergyDensity",
                    row_num,
                    min_value=0.0,
                    max_value=10000.0,
                )
                rec_min = _parse_float(
                    row_norm.get("recommendedchargemin"),
                    "RecommendedChargeMin",
                    row_num,
                    min_value=0.0,
                    max_value=500.0,
                )
                rec_max = _parse_float(
                    row_norm.get("recommendedchargemax"),
                    "RecommendedChargeMax",
                    row_num,
                    min_value=0.0,
                    max_value=500.0,
                )
                if rec_min is not None and rec_max is not None and rec_min > rec_max:
                    raise ValueError(
                        f"Row {row_num}: RecommendedChargeMin cannot exceed RecommendedChargeMax"
                    )
                reference = row_norm.get("reference") or ""
                reference = str(reference).strip() or None
            except ValueError as exc:
                if strict:
                    raise
                errors.append(str(exc))
                continue

            key = _powder_key(name, manufacturer)
            if dedupe and (key in existing_keys or key in seen_keys):
                errors.append(f"Row {row_num}: duplicate powder '{name}' skipped")
                continue
            seen_keys.add(key)

            db_powder = PowderData(
                name=name,
                manufacturer=manufacturer,
                type=powder_type,
                burn_rate=burn_rate,
                energy_density=energy_density,
                recommended_charge_min=rec_min,
                recommended_charge_max=rec_max,
                reference=reference,
            )
            db_session.add(db_powder)
            imported += 1
    db_session.commit()
    for line in format_import_report(file_path, imported, errors):
        print(line)
    return errors


def import_bullet_csv(
    file_path: str,
    db_session: Session,
    strict: bool = True,
    dedupe: bool = True,
) -> list[str]:
    """
    Importer kuledata fra CSV-fil til BulletData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    errors: list[str] = []
    imported = 0
    with open(file_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        if not _validate_required_headers(
            reader.fieldnames,
            ["Name"],
            file_path,
            strict,
            errors,
        ):
            return errors

        existing_keys: set[tuple[str, str, str, str]] = set()
        if dedupe:
            try:
                existing_keys = {
                    _bullet_key(
                        row.name or "", row.manufacturer, row.weight, row.diameter
                    )
                    for row in db_session.query(BulletData).all()
                }
            except Exception:
                existing_keys = set()
        seen_keys: set[tuple[str, str, str, str]] = set()
        for row_num, row in enumerate(reader, start=2):
            try:
                row_norm = _normalize_row(row)
                name = _require_text(row_norm.get("name"), "Name", row_num)
                manufacturer = row_norm.get("manufacturer") or ""
                manufacturer = str(manufacturer).strip() or None
                diameter = _parse_float(
                    row_norm.get("diameter"),
                    "Diameter",
                    row_num,
                    min_value=1.0,
                    max_value=50.0,
                )
                weight = _parse_float(
                    row_norm.get("weight"),
                    "Weight",
                    row_num,
                    min_value=1.0,
                    max_value=2000.0,
                )
                bc = _parse_float(
                    row_norm.get("bc"), "BC", row_num, min_value=0.0, max_value=5.0
                )
                bullet_type = row_norm.get("type") or ""
                bullet_type = str(bullet_type).strip() or None
                length = _parse_float(
                    row_norm.get("length"),
                    "Length",
                    row_num,
                    min_value=1.0,
                    max_value=200.0,
                )
                recommended_twist = _parse_float(
                    row_norm.get("recommendedtwist"),
                    "RecommendedTwist",
                    row_num,
                    min_value=1.0,
                    max_value=50.0,
                )
                reference = row_norm.get("reference") or ""
                reference = str(reference).strip() or None
            except ValueError as exc:
                if strict:
                    raise
                errors.append(str(exc))
                continue

            key = _bullet_key(name, manufacturer, weight, diameter)
            if dedupe and (key in existing_keys or key in seen_keys):
                errors.append(f"Row {row_num}: duplicate bullet '{name}' skipped")
                continue
            seen_keys.add(key)

            db_bullet = BulletData(
                name=name,
                manufacturer=manufacturer,
                diameter=diameter,
                weight=weight,
                bc=bc,
                type=bullet_type,
                length=length,
                recommended_twist=recommended_twist,
                reference=reference,
            )
            db_session.add(db_bullet)
            imported += 1
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
# import_powder_csv('powder_data.csv', session)
# import_bullet_csv('bullet_data.csv', session)
