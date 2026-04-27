# Bullet Master Change Review

- Compared files:
  - `.github/data/exports/bullets_catalog_master.csv`
  - `.github/data/exports/bullets_catalog_master_clean.csv`
- Changed rows: `57`

## Change Buckets

- `54` rows: `display_name` filled or normalized where it was blank.
- `1` row: name spacing normalized and propagated into related fields.
- `2` rows: manufacturer casing normalized and propagated into related fields.

## Field Counts

- `display_name`: `57`
- `name`: `1`
- `manufacturer`: `2`
- `external_ref`: `3`
- `raw_json`: `3`

## Representative Examples

### Display Name Filled

- `id=49`: `Barnes / Match Burner`
  - before: `display_name = ""`
  - after: `display_name = "Barnes Match Burner"`
- `id=3`: `Berger / Hybrid Target`
  - before: `display_name = ""`
  - after: `display_name = "Berger Hybrid Target"`

### Name Spacing Fixed

- `id=98`: `Hornady / Sub-X  #45031`
  - before: `name = "Sub-X  #45031"`
  - after: `name = "Sub-X #45031"`
  - propagated to:
    - `display_name`
    - `external_ref`
    - `raw_json.pname`

### Manufacturer Casing Fixed

- `id=4461`: `RG bullets / CMJ9mm`
  - before: `manufacturer = "RG bullets"`
  - after: `manufacturer = "RG Bullets"`
  - propagated to:
    - `display_name`
    - `external_ref`
    - `raw_json.mname`
- `id=4462`: `RG bullets / HBWC`
  - before: `manufacturer = "RG bullets"`
  - after: `manufacturer = "RG Bullets"`
  - propagated to:
    - `display_name`
    - `external_ref`
    - `raw_json.mname`

## Interpretation

- This cleanup is intentionally conservative.
- It does not attempt semantic reshaping of bullet families or product naming.
- It only fixes verified presentational/data-consistency issues that would otherwise create noisy imports and search results.