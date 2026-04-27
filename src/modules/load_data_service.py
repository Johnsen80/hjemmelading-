"""
Nøytralt service-lag for ladningskort, evidens og referansedata.

Dette er hovedinngangen videre i appen. Historiske moduler beholdes kun som
kompatibilitetslag for eksisterende kode.
"""

from .profile_insights_service import (
    build_load_card_summary,
    build_owned_reference_rows,
    build_profile_evidence_summary,
    build_profile_health_summary,
    build_profile_trust_map,
)


def build_reference_rows(db):
    return build_owned_reference_rows(db)


def build_owned_gordon_rows(db):
    return build_owned_reference_rows(db)


__all__ = [
    "build_load_card_summary",
    "build_profile_health_summary",
    "build_profile_trust_map",
    "build_reference_rows",
    "build_owned_reference_rows",
    "build_owned_gordon_rows",
    "build_profile_evidence_summary",
]
