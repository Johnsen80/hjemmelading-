# SAAMI Rifle Seed Notes

Denne seed-filen er et lite, eksplisitt `official_saami`-lag for patronstandarder som ikke er avhengig av Gordon/GRT.

Kilder brukt:
- SAAMI standards landing page: https://saami.org/technical-information/ansi-saami-standards/
- SAAMI rifle standard PDF (2025 Z299.4): `SAAMI-Z299.4-CFR-2025-Centerfire-Rifle-Approved-2-10-2025.pdf`
- SAAMI 2015 velocity/pressure table PDF: `ANSI-SAAMI-Z299.4-CFR-Approved-2015-12-14-Posting-Copy.pdf`

Seeden inneholder foreløpig bare et lite utvalg vanlige riflepatroner:
- `223 Remington`
- `300 AAC Blackout`
- `6.5 Creedmoor`
- `308 Winchester`

Prinsipper:
- `source_kind=official_saami`
- `evidence_level=official_standard`
- dimensjoner er tatt fra offisielle SAAMI-tegninger
- `max_pressure_psi` er hentet fra SAAMI pressure/velocity-tabeller
- felt som ikke er eksplisitt løftet fra kilden er bevisst latt stå tomme

Dette er ment som et startpunkt for et større SAAMI-lag, ikke en komplett SAAMI-katalog.

I tillegg finnes en separat seed for nylig aksepterte riflepatroner:
- [saami_newly_accepted_rifle_cartridges.csv](./saami_newly_accepted_rifle_cartridges.csv)
- [saami_rifle_acceptance_announcements.csv](./saami_rifle_acceptance_announcements.csv)

Der brukes:
- `evidence_level=official_prestandard` når SAAMI har publisert en offisiell introduction package eller akseptmelding, men patronen ikke nødvendigvis er løftet inn i neste samlede standard-PDF ennå.
- `evidence_level=official_announcement` når vi bare har en offisiell SAAMI-akseptmelding med patronnavn og trykk, men ikke en løftet full tegning ennå.
