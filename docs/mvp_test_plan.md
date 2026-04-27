# MVP Test Plan

## Scope
Verify MVP flows for chronograph, target analysis, load testing, import/export, and UI cohesion on Windows desktop.

## Principles
- Offline-first: tests must pass without network.
- Stable units and locale: input accepts local formats; storage and exports are stable.
- Reproducible: use golden data for regression.

## Test matrix
### Chronograph import (CSV/TXT)
- Import LabRadar CSV with semicolon delimiter and temperature column.
- Import Garmin Xero CSV with alternate header names.
- Import MagnetoSpeed TXT/CSV and confirm velocities are parsed.
- Verify stats: avg, ES, SD match golden data.
- Verify locale decimal handling (comma vs dot).

### Target analysis (JPG/PNG)
- Load a calibrated target image and verify group size, MOA, offsets.
- Validate perspective/rotation correction path.
- Check hole detection robustness on low contrast images.
- Regression: compare results to golden image set.

### Load testing and history
- Create a ladder test session and save results.
- Create a temperature ladder test and compare windows.
- Confirm results link to rifle/ammo profile.
- Verify history view shows prior sessions and comparisons.

### Import/export
- Export CSV/JSON with versioned schema fields.
- Re-import exported data and compare values (round-trip).
- Confirm units are stable in export and locale does not leak.

### App shell and UX
- Verify workflows are reachable from main navigation.
- Empty-state messaging appears when datasets are missing.
- Terminology is consistent across navigation and dialogs.

### Units and locale
- Input: mm/in, fps/mps conversions in UI.
- Storage: internal normalized units.
- Output: locale formatting in UI, stable formatting in exports.

### i18n (Norwegian/English)
- Switch language in Settings and verify full UI update.
- Check missing-key fallback behavior is visible in dev builds.
- Confirm key workflows render in both languages.

## Test data
- Golden chronograph samples: [tests/data/golden/chronograph/labradar_sample.csv](tests/data/golden/chronograph/labradar_sample.csv), [tests/data/golden/chronograph/garmin_xero_sample.csv](tests/data/golden/chronograph/garmin_xero_sample.csv), [tests/data/golden/chronograph/magnetospeed_sample.txt](tests/data/golden/chronograph/magnetospeed_sample.txt), [tests/data/golden/chronograph/magnetospeed_sample.csv](tests/data/golden/chronograph/magnetospeed_sample.csv), [tests/data/golden/chronograph/expected_stats.json](tests/data/golden/chronograph/expected_stats.json)
- Golden target placeholders: [tests/data/golden/targets/target_sample.ppm](tests/data/golden/targets/target_sample.ppm), [tests/data/golden/targets/expected_metrics.json](tests/data/golden/targets/expected_metrics.json)
- Load test placeholders: [tests/data/golden/load_tests/README.md](tests/data/golden/load_tests/README.md)

## Exit criteria
- No P0 failures in MVP flows.
- Round-trip import/export matches original values.
- Golden data results within tolerance.
