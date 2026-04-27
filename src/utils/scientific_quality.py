from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_iso_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for candidate in (text, text.replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _extract_environment_quality(environment: Any) -> tuple[float, str]:
    if environment is None:
        return (
            0.0,
            "Miljødata mangler som eget input og regnes foreløpig som standardatmosfære.",
        )

    source_names = (
        "temperature_source",
        "pressure_source",
        "humidity_source",
        "altitude_source",
    )
    measured_count = 0
    assumed_count = 0
    for name in source_names:
        source = str(getattr(environment, name, "") or "").strip().lower()
        if not source:
            continue
        if source in {"measured", "observed", "sensor", "weather"}:
            measured_count += 1
        else:
            assumed_count += 1

    if measured_count >= 2:
        return (
            1.0,
            "Miljødata er delvis målt og kan gi mer troverdig density altitude og ballistikk.",
        )
    if measured_count == 1 or assumed_count:
        return (
            0.5,
            "Miljødata finnes, men bygger helt eller delvis på antatte standardverdier.",
        )
    return 0.0, "Miljødata mangler tydelig kilde og bør regnes som svake."


def build_input_quality_summary(
    workflow_data: dict[str, Any] | None,
    observations: dict[str, Any] | None,
    bullet_data: dict[str, Any] | None = None,
    environment: Any | None = None,
) -> dict[str, Any]:
    workflow_data = workflow_data or {}
    observations = observations or {}
    bullet_data = bullet_data or {}

    score = 0.0
    checks: list[str] = []

    chrono_rows = observations.get("chronograph_sessions") or []
    chrono_count = len(chrono_rows)
    if chrono_count >= 3:
        score += 1.5
        checks.append(f"Chrono: {chrono_count} serier gir brukbar hastighetsdekning.")
    elif chrono_count >= 1:
        score += 0.75
        checks.append(
            f"Chrono: {chrono_count} serie finnes, men hastighetsbildet er fortsatt tynt."
        )
    else:
        checks.append(
            "Chrono: mangler egne serier, så hastighet og ES/SD er foreløpig svakt forankret."
        )

    have_group = isinstance(observations.get("best_group_mm"), (int, float))
    shooting_rows = observations.get("shooting_sessions") or []
    if have_group or shooting_rows:
        score += 1.0
        checks.append("Presisjon: workflowet har faktisk gruppedata fra skyting.")
    else:
        checks.append(
            "Presisjon: mangler gruppedata, så node- og treffvurdering blir mer usikker."
        )

    bc_g7 = bullet_data.get("bc_g7")
    bc_g1 = bullet_data.get("bc_g1")
    if isinstance(bc_g7, (int, float)):
        score += 1.0
        checks.append(
            "Dragdata: BC G7 er kjent og gir bedre utgangspunkt for moderne kuleformer."
        )
    elif isinstance(bc_g1, (int, float)):
        score += 0.75
        checks.append(
            "Dragdata: bare BC G1 er kjent, så dragbildet er brukbart men mindre presist."
        )
    else:
        checks.append("Dragdata: BC mangler, så ballistiske råd må leses konservativt.")

    env_score, env_message = _extract_environment_quality(environment)
    score += env_score
    checks.append(f"Miljø: {env_message}")

    if workflow_data.get("rifle_id") and workflow_data.get("bullet_id"):
        score += 0.5
        checks.append("Kontekst: rifle og kule er eksplisitt koblet i workflowet.")
    else:
        checks.append(
            "Kontekst: våpen- og kulekobling er ikke fullt eksplisitt i datagrunnlaget."
        )

    created_date = _parse_iso_date(
        workflow_data.get("created_date") or workflow_data.get("test_date")
    )
    latest_session = None
    for row in chrono_rows:
        candidate = _parse_iso_date(row.get("session_date") or row.get("date"))
        if candidate and (latest_session is None or candidate > latest_session):
            latest_session = candidate
    if created_date and latest_session:
        age_days = abs((latest_session - created_date).days)
        if age_days <= 45:
            score += 0.5
            checks.append(
                f"Ferskhet: måleseriene ligger tett på workflowstart ({age_days} dager)."
            )
        else:
            checks.append(
                f"Ferskhet: siste måleserie ligger {age_days} dager fra workflowstart og bør leses med litt mer varsomhet."
            )
    elif latest_session:
        score += 0.25
        checks.append(
            "Ferskhet: måleserier finnes, men workflowet mangler tydelig startdato for sammenligning."
        )
    else:
        checks.append(
            "Ferskhet: ingen daterte måleserier tilgjengelig for å vurdere hvor aktuell læringen er."
        )

    if score >= 4.0:
        level = "high"
        title = "Høy inputkvalitet"
        message = "Datagrunnlaget er bredt nok til at råd og modeller kan leses med relativt god tillit."
    elif score >= 2.5:
        level = "medium"
        title = "Brukbar inputkvalitet"
        message = (
            "Datagrunnlaget er nyttig, men noen felt er fortsatt antatte eller tynne."
        )
    else:
        level = "low"
        title = "Lav inputkvalitet"
        message = "Datagrunnlaget er for tynt eller for antatt til at sterke råd bør gis uten ekstra verifisering."

    return {
        "level": level,
        "title": title,
        "message": message,
        "score": round(score, 2),
        "checks": checks[:5],
    }
