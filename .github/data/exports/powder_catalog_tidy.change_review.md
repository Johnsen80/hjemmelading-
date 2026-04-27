# Powder Catalog Change Review

- Compared files:
  - `.github/data/exports/powder_catalog_master.csv`
  - `.github/data/exports/powder_catalog_tidy.csv`
- Master rows: `258`
- Tidy rows: `258`
- Shared key rows: `258`
- Changed rows: `256`
- Master-only rows: `0`
- Tidy-only rows: `0`

## Change Buckets

- `256` rows: presentation/source metadata changes only.
- `0` rows: detected core numeric changes in the compared review fields.
- `0` rows: detected evidence-level or notes changes.

## Field Counts

- `source_label`: `256`

## Representative Examples

### Source Label Removed In Tidy Export

- `Accurate / 1680`
  - before: `source_label = "Gordon memory dump"`
  - after: `source_label = ""`
- `Accurate / 2015`
  - before: `source_label = "Gordon memory dump"`
  - after: `source_label = ""`
- `Accurate / 2230`
  - before: `source_label = "Gordon memory dump"`
  - after: `source_label = ""`

## Structural Difference

- `powder_catalog_master.csv` is a full export with many provenance, raw-model, and simulation columns.
- `powder_catalog_tidy.csv` is a heavily reduced projection focused on user-facing/core powder fields.
- In the compared overlap, the only detected content change is that `source_label` is blank in the tidy export for `256` rows.

## Interpretation

- This is not the same kind of cleanup as the bullet master cleanup.
- The tidy powder file currently behaves more like a trimmed presentation/export view than a corrected canonical dataset.
- Based on this comparison alone, there is no sign that `powder_catalog_tidy.csv` fixes burn-rate, density, or other core powder values relative to master.
- If the goal is a true cleaned powder source of truth, the next step should be a dedicated powder cleanup pass with explicit normalization rules rather than treating `powder_catalog_tidy.csv` as equivalent to a cleaned master.