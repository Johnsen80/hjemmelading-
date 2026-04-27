# Component Catalog Health Report

## Summary

- Next cleanup candidate: `bullets`
- High-priority catalogs: `none`
- Catalogs ready for sync: `bullets, powders, cases, primers`
- Catalogs blocking sync: `none`

## Bullets

- Rows: `5824`
- Noise score: `110`
- Priority: `high`
- Effective priority: `medium`
- Clean artifact present: `True`
- Catalog sync ready: `True`
- Operational status: `ready_for_sync`
- Blank display_name: `54`
- Blank source_label: `54`
- Manufacturer variant groups: `1`
- Raw JSON parse failures: `0`
- Raw JSON name mismatches: `0`
- Duplicate key groups: `463`
- Recommendation: Raw master still has historical noise, but a clean export already exists and should be treated as the operational source.
- Operational recommendation: Catalog is suitable as an operational sync source under current regression monitoring.

Manufacturer variant examples:
- `rg bullets`: `{'RG Bullets': 1, 'RG bullets': 2}`

## Powders

- Rows: `258`
- Noise score: `4`
- Priority: `high`
- Effective priority: `medium`
- Clean artifact present: `True`
- Catalog sync ready: `True`
- Operational status: `ready_for_sync`
- Blank display_name: `0`
- Blank source_label: `2`
- Manufacturer variant groups: `1`
- Raw JSON parse failures: `0`
- Raw JSON name mismatches: `1`
- Duplicate key groups: `0`
- Recommendation: Raw master still has historical noise, but a clean export already exists and should be treated as the operational source.
- Operational recommendation: Catalog is suitable as an operational sync source under current regression monitoring.

Manufacturer variant examples:
- `vectan`: `{'VECTAN': 1, 'Vectan': 14}`

## Cases

- Rows: `3`
- Noise score: `0`
- Priority: `low`
- Effective priority: `low`
- Clean artifact present: `False`
- Catalog sync ready: `True`
- Operational status: `ready_for_sync`
- Blank display_name: `0`
- Blank source_label: `0`
- Manufacturer variant groups: `0`
- Raw JSON parse failures: `0`
- Raw JSON name mismatches: `0`
- Duplicate key groups: `0`
- Recommendation: Catalog looks stable; keep it under regression monitoring only.
- Operational recommendation: Catalog is suitable as an operational sync source under current regression monitoring.

## Primers

- Rows: `24`
- Noise score: `0`
- Priority: `low`
- Effective priority: `low`
- Clean artifact present: `False`
- Catalog sync ready: `True`
- Operational status: `ready_for_sync`
- Blank display_name: `0`
- Blank source_label: `0`
- Manufacturer variant groups: `0`
- Raw JSON parse failures: `0`
- Raw JSON name mismatches: `0`
- Duplicate key groups: `0`
- Recommendation: Catalog looks stable; keep it under regression monitoring only.
- Operational recommendation: Catalog is suitable as an operational sync source under current regression monitoring.
