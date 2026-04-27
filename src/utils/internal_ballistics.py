from __future__ import annotations

from typing import Any

from .pressure_calculator import PressureCalculator


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def estimate_burn_completeness(
    *,
    barrel_length_in: float | None = None,
    load_density_percent: float | None = None,
    burn_rate_position: str | None = None,
) -> float | None:
    density = _coerce_float(load_density_percent)
    length = _coerce_float(barrel_length_in)
    if density is None and length is None and not burn_rate_position:
        return None

    score = 82.0
    if density is not None:
        if density < 75:
            score -= 12.0
        elif density < 85:
            score -= 6.0
        elif density <= 102:
            score += 5.0
        elif density <= 108:
            score += 1.0
        else:
            score -= 4.0

    if length is not None:
        score += (length - 20.0) * 1.2

    position = str(burn_rate_position or "").strip().lower()
    if position == "slow":
        if length is not None and length < 20.0:
            score -= 8.0
        elif length is not None and length >= 24.0:
            score += 3.0
    elif position == "fast":
        if length is not None and length < 20.0:
            score += 2.0
        elif length is not None and length >= 26.0:
            score -= 2.0

    return round(_clamp(score, 55.0, 99.0), 1)


def build_internal_ballistics_summary(
    *,
    charge_weight_gr: float | None = None,
    powder_name: str | None = None,
    case_capacity_gr_h2o: float | None = None,
    case_capacity_ml: float | None = None,
    barrel_length_in: float | None = None,
    load_density_percent: float | None = None,
    powder_volume_ml: float | None = None,
    available_volume_ml: float | None = None,
    powder_density_g_ml: float | None = None,
    burn_rate_position: str | None = None,
    qex_kj_per_kg: float | None = None,
    k_ratio: float | None = None,
    temp_stable: bool | int | None = None,
    validation_status: str | None = None,
    usable_for_simulation: bool | int | None = None,
    pressure_margin_percent: float | None = None,
) -> dict[str, Any]:
    density = _coerce_float(load_density_percent)
    if density is None:
        charge = _coerce_float(charge_weight_gr)
        capacity = _coerce_float(case_capacity_gr_h2o)
        if charge is not None and capacity is not None and powder_name:
            density = PressureCalculator().calculate_load_density(
                charge, str(powder_name), capacity
            )

    powder_volume = _coerce_float(powder_volume_ml)
    available_volume = _coerce_float(available_volume_ml)
    case_capacity_volume = _coerce_float(case_capacity_ml)
    powder_density = _coerce_float(powder_density_g_ml)
    qex_value = _coerce_float(qex_kj_per_kg)
    k_value = _coerce_float(k_ratio)
    pressure_margin = _coerce_float(pressure_margin_percent)
    powder_validation = str(validation_status or "").strip().lower()
    compression_ratio: float | None = None
    if powder_volume and available_volume and powder_volume > 0:
        compression_ratio = round(available_volume / powder_volume, 3)
    elif density and density > 0:
        compression_ratio = round(100.0 / density, 3)

    burn_completeness = estimate_burn_completeness(
        barrel_length_in=barrel_length_in,
        load_density_percent=density,
        burn_rate_position=burn_rate_position,
    )

    if density is None:
        return {
            "level": "neutral",
            "title": "Internballistikk",
            "message": "Mangler nok data til fyllratevurdering. Legg inn H2O/case capacity, startladning og kruttkontekst.",
            "metrics": [],
            "checks": [
                "Fyllrate krever minst case capacity og ladningsvekt.",
                "Forbrent andel vises bare som modellert estimat, ikke malt sannhet.",
            ],
        }

    metrics: list[dict[str, str]] = [
        {"name": "Fyllrate", "value": f"{density:.1f}%"},
    ]
    if case_capacity_volume is not None:
        metrics.append(
            {"name": "Hylsevolum", "value": f"{case_capacity_volume:.2f} ml"}
        )
    if powder_density is not None:
        metrics.append({"name": "Krutttetthet", "value": f"{powder_density:.2f} g/ml"})
    if qex_value is not None:
        metrics.append({"name": "Energi", "value": f"{qex_value:.0f} kJ/kg"})
    if k_value is not None:
        metrics.append({"name": "k-ratio", "value": f"{k_value:.3f}"})
    if temp_stable in (True, 1, "1"):
        metrics.append({"name": "Temp-stabil", "value": "ja"})
    elif temp_stable in (False, 0, "0"):
        metrics.append({"name": "Temp-stabil", "value": "nei"})
    checks: list[str] = []
    level = "ok"

    if compression_ratio is not None:
        metrics.append({"name": "Kompresjon", "value": f"{compression_ratio:.2f}x"})

    if burn_completeness is not None:
        metrics.append(
            {
                "name": "Forbrent andel",
                "value": f"{burn_completeness:.0f}% modellert",
            }
        )

    if density < 80:
        level = "warning"
        checks.append(
            "Lav fyllrate kan gi mer orienteringsfolsomhet, mer ES og mindre jevn forbrenning."
        )
    elif density < 90:
        level = "warning"
        checks.append(
            "Fyllraten er brukbar, men fortsatt litt lav for et tydelig internballistisk sweet spot."
        )
    elif density <= 103:
        checks.append(
            "Fyllraten ligger i et sunt arbeidsvindu for jevn forbrenning og praktisk QA."
        )
    elif density <= 108:
        level = "warning"
        checks.append(
            "Hoy fyllrate. Verifiser seating, trykktegn og lotrespons ekstra noyaktig."
        )
    else:
        level = "critical"
        checks.append(
            "Ladningen ser komprimert ut. Behandle den som hoyrisiko og verifiser konservativt."
        )

    if burn_completeness is not None:
        if burn_completeness < 78:
            if level == "ok":
                level = "critical"
            checks.append(
                "Modellert forbrenningsgrad er lav. Kort pipe eller treg kombinasjon kan gi uforbrent krutt og lavere effektivitet."
            )
        elif burn_completeness < 88:
            if level == "ok":
                level = "warning"
            checks.append(
                "Forbrent andel ser moderat ut. Det er lurt aa bekrefte velocity og munningssignatur i praksis."
            )
        else:
            checks.append(
                "Forbrent andel ser brukbar ut for denne pipe-/fyllrate-kombinasjonen."
            )

    if qex_value is not None:
        if qex_value < 3300:
            checks.append(
                "Lav energitetthet peker mot roligere fartspotensial og mindre effektiv forbrenning i store hylser."
            )
        elif qex_value > 4200:
            checks.append(
                "Hoy energitetthet: bekreft trykkrespons og lotoppforsel konservativt."
            )

    if k_value is not None:
        if k_value < 1.18:
            checks.append(
                "Lav k-ratio kan gi et mykere trykkforlop, men bor bekreftes mot malt fart."
            )
        elif k_value > 1.28:
            checks.append(
                "Hoy k-ratio kan gi en skarpere trykkurve. Sma charge-endringer bor behandles konservativt."
            )

    if temp_stable in (False, 0, "0"):
        if level == "ok":
            level = "warning"
        checks.append(
            "Kruttet er ikke markert som temperaturstabilt. Verifiser fart og trykk i varmt og kaldt vare."
        )
    elif temp_stable in (True, 1, "1"):
        checks.append(
            "Kruttet er markert som temperaturstabilt, men bor fortsatt bekreftes i praksis."
        )

    if powder_validation and powder_validation not in {
        "verified",
        "validated",
        "trusted",
    }:
        checks.append(
            f"Kruttmodellen er markert som {powder_validation}. Bruk ekstra malt data ved finjustering."
        )
        if powder_validation in {"memory_extracted", "unverified"} and level == "ok":
            level = "warning"

    if usable_for_simulation in (False, 0, "0"):
        level = "warning" if level == "ok" else level
        checks.append(
            "Kruttprofilen er ikke eksplisitt godkjent for simulering. Bruk den som referanse, ikke fasit."
        )

    if pressure_margin is not None:
        if pressure_margin < 10:
            checks.append(
                "Kombinasjonen av fyllingsgrad og trykkmargin tilsier hoy konservatisme."
            )
        elif pressure_margin < 15:
            checks.append(
                "Trykkmarginen er smal. Smale charge-steg er lurt selv om forbrenningen ser jevn ut."
            )

    if powder_density is None:
        checks.append(
            "Krutttetthet er ikke eksplisitt kjent i denne vurderingen. Fyllrate bygger da mer på standardantakelser."
        )

    message = (
        f"Fyllrate {density:.1f}%"
        + (
            f", kompresjon {compression_ratio:.2f}x"
            if compression_ratio is not None
            else ""
        )
        + (
            f", modellert forbrent andel {burn_completeness:.0f}%."
            if burn_completeness is not None
            else "."
        )
    )

    if qex_value is not None:
        message += f" Energi {qex_value:.0f} kJ/kg."
    if temp_stable in (False, 0, "0"):
        message += " Temperaturfolsomhet bor verifiseres."

    return {
        "level": level,
        "title": "Internballistikk",
        "message": message,
        "metrics": metrics,
        "checks": checks,
        "load_density_percent": density,
        "compression_ratio": compression_ratio,
        "burn_completeness_percent": burn_completeness,
        "qex_kj_per_kg": qex_value,
        "k_ratio": k_value,
        "temp_stable": temp_stable,
        "validation_status": validation_status,
        "usable_for_simulation": usable_for_simulation,
        "pressure_margin_percent": pressure_margin,
    }


def format_internal_ballistics_text(summary: dict[str, object]) -> list[str]:
    if not summary:
        return []
    lines = [str(summary.get("title") or "Internballistikk")]
    message = str(summary.get("message") or "").strip()
    if message:
        lines.append(message)
    for metric in summary.get("metrics") or []:
        if isinstance(metric, dict):
            name = str(metric.get("name") or "").strip()
            value = str(metric.get("value") or "").strip()
            if name and value:
                lines.append(f"{name}: {value}")
    for context_line in summary.get("context_lines") or []:
        text = str(context_line or "").strip()
        if text:
            lines.append(text)
    return lines
