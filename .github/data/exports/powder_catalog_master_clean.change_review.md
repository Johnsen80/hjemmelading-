# Powder Master Change Review

- Compared files:
  - `.github/data/exports/powder_catalog_master.csv`
  - `.github/data/exports/powder_catalog_master_clean.csv`
- Changed rows: `2`

## Change Buckets

- `1` row: manufacturer casing normalized and propagated into related fields.
- `1` row: display-name/model-name capitalization normalized and propagated into related fields.

## Field Counts

- `display_name`: `2`
- `external_ref`: `2`
- `raw_json`: `2`
- `manufacturer`: `1`

## Representative Examples

### Manufacturer Casing Fixed

- `id=217`: `VECTAN / SP 11`
  - before: `manufacturer = "VECTAN"`
  - after: `manufacturer = "Vectan"`
  - propagated to:
    - `display_name`
    - `external_ref`
    - `raw_json.mname`

### Product Name Capitalization Fixed

- `id=95`: `Hodgdon / LeverEvolution`
  - before: `display_name = "Hodgdon Leverevolution"`
  - after: `display_name = "Hodgdon LeverEvolution"`
  - propagated to:
    - `external_ref`
    - `raw_json.pname`

## Interpretation

- This cleanup is intentionally conservative.
- It does not change burn rate, density, or simulation parameters.
- It only fixes verified naming/casing inconsistencies so the powder catalog stays consistent without changing the engine-relevant powder model data.