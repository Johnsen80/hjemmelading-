"""Extract a WeaponBallisticProfile from the database and learning data.

Priority chain for BC (highest quality wins):
  1. CDM curve back-calculated from multi-range drop measurements (cdm_calibrator)
  2. G7 BC back-solved from single impact measurement at known range
  3. bc_g7 from ammo_profile row
  4. bc_g7 from linked bullet row
  5. bc_g1 from ammo_profile (converted via standard G1→G7 factor)
  6. Default safe fallback (0.200 G7)

Priority chain for MV:
  1. Weighted mean of chrono sessions (weighted by shot count, filtered to active lot)
  2. velocity_fps from ammo_profile row
  3. Default safe fallback (800 m/s)
"""

from __future__ import annotations

import json
import math
from typing import Any

from ..field_planning.models import WeaponBallisticProfile

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_weapon_ballistic_profile(
    db: Any,
    rifle_id: int,
    ammo_profile_id: int | None = None,
    load_session_id: int | None = None,
) -> WeaponBallisticProfile:
    """Build a WeaponBallisticProfile from DB data + load session learning.

    Parameters
    ----------
    db:
        Database instance (has .execute_query()).
    rifle_id:
        Primary key of the rifle.
    ammo_profile_id:
        If provided, use this ammo profile for BC/bullet data.
    load_session_id:
        If provided, extract learning data (calibrated BC, MV temperature curve)
        from the load development session.
    """
    rifle = _load_rifle(db, rifle_id)
    ammo = _load_ammo_profile(db, ammo_profile_id) if ammo_profile_id else {}
    bullet = _load_bullet(db, ammo.get("bullet_id")) if ammo.get("bullet_id") else {}
    optic = _load_active_optic(db, rifle_id)
    chrono_sessions = _load_chrono_sessions(db, ammo_profile_id, rifle_id)
    learning = _load_learning_state(db, load_session_id) if load_session_id else {}

    # --- MV ---
    mv_fps, mv_sd_fps, mv_source, mv_temp_curve = _resolve_mv(
        chrono_sessions, ammo, learning
    )

    # --- BC ---
    learned_bc, bc_type, bc_source = _resolve_bc(ammo, bullet, learning)

    # --- physical ---
    twist_in = _safe_float(rifle.get("twist_rate_inches")) or 10.0
    twist_dir = str(rifle.get("twist_direction") or "RIGHT").upper()
    if twist_dir not in {"RIGHT", "LEFT"}:
        twist_dir = "RIGHT"

    sight_mm = (
        _safe_float(optic.get("height_mm"))
        or _safe_float(rifle.get("scope_height_mm"))
        or 38.0
    )
    zero_m = _safe_float(optic.get("zero_distance")) or 100.0

    bullet_dia_mm = (
        _safe_float(bullet.get("diameter_mm"))
        or _safe_float(ammo.get("caliber_mm"))
        or 0.0
    )
    bullet_len_mm = _safe_float(bullet.get("length_mm")) or 0.0
    bullet_mass_gr = (
        _safe_float(bullet.get("weight_grains"))
        or _safe_float(ammo.get("bullet_weight"))
        or 0.0
    )

    cold_bore_moa, cold_bore_n = _resolve_cold_bore(learning)

    ammo_label = _build_ammo_label(ammo, bullet)

    return WeaponBallisticProfile(
        rifle_id=rifle_id,
        rifle_name=str(rifle.get("name") or f"Rifle {rifle_id}"),
        caliber=str(rifle.get("caliber") or ammo.get("caliber") or ""),
        barrel_configuration_id=str(rifle.get("barrel_configuration_id") or "").strip()
        or None,
        twist_rate_in=twist_in,
        twist_direction=twist_dir,
        sight_height_mm=sight_mm,
        zero_distance_m=zero_m,
        learned_mv_fps=mv_fps,
        learned_mv_sd_fps=mv_sd_fps,
        learned_bc=learned_bc,
        learned_bc_type=bc_type,
        bc_source=bc_source,
        mv_source=mv_source,
        mv_temperature_curve=mv_temp_curve,
        cold_bore_offset_moa=cold_bore_moa,
        cold_bore_sample_count=cold_bore_n,
        bullet_diameter_mm=bullet_dia_mm,
        bullet_length_mm=bullet_len_mm,
        bullet_mass_gr=bullet_mass_gr,
        ammo_profile_id=ammo_profile_id,
        ammo_label=ammo_label,
    )


# ---------------------------------------------------------------------------
# DB loaders
# ---------------------------------------------------------------------------


def _load_rifle(db: Any, rifle_id: int) -> dict:
    rows = db.execute_query("SELECT * FROM rifles WHERE id = ?", (rifle_id,))
    return rows[0] if rows else {}


def _load_ammo_profile(db: Any, ammo_profile_id: int) -> dict:
    rows = db.execute_query(
        "SELECT * FROM ammo_profiles WHERE id = ?", (ammo_profile_id,)
    )
    return rows[0] if rows else {}


def _load_bullet(db: Any, bullet_id: int) -> dict:
    rows = db.execute_query("SELECT * FROM bullets WHERE id = ?", (bullet_id,))
    return rows[0] if rows else {}


def _load_active_optic(db: Any, rifle_id: int) -> dict:
    rows = db.execute_query(
        "SELECT * FROM optics WHERE rifle_id = ? ORDER BY id DESC LIMIT 1",
        (rifle_id,),
    )
    return rows[0] if rows else {}


def _load_chrono_sessions(
    db: Any,
    ammo_profile_id: int | None,
    rifle_id: int,
) -> list[dict]:
    if ammo_profile_id:
        rows = db.execute_query(
            """SELECT avg_velocity_fps, sd_fps, es_fps, shot_count, temperature_f
               FROM chronograph_sessions
               WHERE ammo_profile_id = ?
               ORDER BY session_date DESC
               LIMIT 20""",
            (ammo_profile_id,),
        )
        if rows:
            return rows
    # Fallback: any session linked to this rifle via ammo_profiles
    rows = db.execute_query(
        """SELECT cs.avg_velocity_fps, cs.sd_fps, cs.es_fps, cs.shot_count, cs.temperature_f
           FROM chronograph_sessions cs
           JOIN ammo_profiles ap ON cs.ammo_profile_id = ap.id
           WHERE ap.rifle_id = ?
           ORDER BY cs.session_date DESC
           LIMIT 10""",
        (rifle_id,),
    )
    return rows or []


def _load_learning_state(db: Any, load_session_id: int) -> dict:
    rows = db.execute_query(
        "SELECT learning_state_json FROM load_development_sessions WHERE id = ?",
        (load_session_id,),
    )
    if not rows:
        return {}
    raw = rows[0].get("learning_state_json") or "{}"
    try:
        return json.loads(raw) if isinstance(raw, str) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------


def _resolve_mv(
    sessions: list[dict],
    ammo: dict,
    learning: dict,
) -> tuple[float, float, str, list[tuple[float, float]]]:
    """Return (mv_fps, sd_fps, source, temperature_curve)."""

    # Build temperature curve from all sessions that have both temp and MV
    temp_mv_pairs: list[tuple[float, float]] = []
    for s in sessions:
        mv = _safe_float(s.get("avg_velocity_fps"))
        temp_f = _safe_float(s.get("temperature_f"))
        if mv and mv > 100 and temp_f is not None:
            temp_c = (temp_f - 32) * 5 / 9
            temp_mv_pairs.append((temp_c, mv))

    temp_mv_pairs.sort(key=lambda x: x[0])

    # Weighted mean MV (weight by shot_count)
    if sessions:
        total_weight = 0.0
        weighted_mv = 0.0
        weighted_var = 0.0
        for s in sessions:
            mv = _safe_float(s.get("avg_velocity_fps"))
            sd = _safe_float(s.get("sd_fps")) or 0.0
            n = max(1, int(s.get("shot_count") or 5))
            if mv and mv > 100:
                weighted_mv += mv * n
                weighted_var += (sd * sd) * n
                total_weight += n
        if total_weight > 0:
            mean_mv = weighted_mv / total_weight
            pooled_sd = math.sqrt(weighted_var / total_weight)
            return mean_mv, pooled_sd, "chrono_sessions", temp_mv_pairs

    # Fallback to ammo profile
    mv = _safe_float(ammo.get("velocity_fps"))
    if mv and mv > 100:
        return mv, 10.0, "ammo_profile", []

    # Safe fallback
    return 800.0 * 3.28084, 15.0, "default", []


def _resolve_bc(
    ammo: dict,
    bullet: dict,
    learning: dict,
) -> tuple[float, str, str]:
    """Return (bc_value, bc_type, source_label)."""

    # 1. CDM calibrated BC in learning state
    calibrated = learning.get("calibrated_bc") or {}
    if isinstance(calibrated, dict):
        bc = _safe_float(calibrated.get("bc_g7"))
        if bc and bc > 0.05:
            return bc, "G7", "measured_drops"

    # 2. G7 from ammo profile
    bc = _safe_float(ammo.get("bc_g7"))
    if bc and bc > 0.05:
        return bc, "G7", "ammo_profile"

    # 3. G7 from bullet
    bc = _safe_float(bullet.get("bc_g7"))
    if bc and bc > 0.05:
        return bc, "G7", "bullet_library"

    # 4. G1 from ammo profile → convert to approximate G7
    bc_g1 = _safe_float(ammo.get("bc_g1"))
    if bc_g1 and bc_g1 > 0.05:
        return bc_g1 * 0.47, "G7", "ammo_profile_g1_converted"

    # 5. G1 from bullet
    bc_g1 = _safe_float(bullet.get("bc_g1"))
    if bc_g1 and bc_g1 > 0.05:
        return bc_g1 * 0.47, "G7", "bullet_library_g1_converted"

    # Safe fallback
    return 0.200, "G7", "default"


def _resolve_cold_bore(learning: dict) -> tuple[float, int]:
    """Return (cold_bore_offset_moa, sample_count)."""
    cb = learning.get("cold_bore") or {}
    if not isinstance(cb, dict):
        return 0.0, 0
    offset = _safe_float(cb.get("offset_moa")) or 0.0
    n = int(cb.get("sample_count") or 0)
    return offset, n


def _build_ammo_label(ammo: dict, bullet: dict) -> str:
    parts = []
    name = str(ammo.get("name") or "").strip()
    if name:
        parts.append(name)
    bullet_name = str(bullet.get("name") or "").strip()
    if bullet_name and bullet_name not in name:
        weight = bullet.get("weight_grains")
        if weight:
            parts.append(f"{bullet_name} {weight}gr")
        else:
            parts.append(bullet_name)
    return " / ".join(parts) if parts else "Unknown ammo"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None
