"""
Nøytral hovedinngang for ladningsinnsikt, evidens, helse og tillitskart.

Denne modulen er ment å være produktets primære tjenestelag for
profiloppsummeringer. Eldre moduler med historiske navn beholdes foreløpig
kun som kompatibilitetslag.
"""

from .reference_owned_data_service import (
    build_load_card_summary,
    build_owned_reference_rows,
    build_profile_evidence_summary,
    build_profile_health_summary,
    build_profile_trust_map,
)


def build_owned_gordon_rows(db):
    return build_owned_reference_rows(db)


__all__ = [
    "build_load_card_summary",
    "build_owned_reference_rows",
    "build_owned_gordon_rows",
    "build_profile_evidence_summary",
    "build_profile_health_summary",
    "build_profile_trust_map",
]
