from __future__ import annotations

import xml.etree.ElementTree as ET


def _safe_float(value: str | None) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except Exception:
        return None


def import_grtload_xml(file_path: str, db_session, strict: bool = False) -> list[str]:
    errors: list[str] = []
    tree = ET.parse(file_path)
    root = tree.getroot()

    for powder in root.findall(".//Powder"):
        minimum = _safe_float(powder.findtext("RecommendedChargeMin"))
        maximum = _safe_float(powder.findtext("RecommendedChargeMax"))
        if minimum is not None and maximum is not None and minimum > maximum:
            errors.append("RecommendedChargeMin cannot exceed RecommendedChargeMax")

    try:
        db_session.commit()
    except Exception:
        if strict:
            raise

    return errors


__all__ = ["import_grtload_xml"]
