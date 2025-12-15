Inventory & QC Design — Valkyrie Ballistics

Goals
- Allow users to add components (bullets, powders, cases, primers) and register inventory lots.
- Allow QC measurement sessions for bullets/cases: weigh & measure a sample (min 10) or entire lot.
- Compute mean, SD, median, min, max, 95% CI, and flag outliers (>3σ default).
- Track brass lifecycle and prep sessions (anneal, trim, neck tension settings).
- Keep UI simple: wizards for Add Lot, QC Measurement, Brass Prep.

Data model (proposed)
- `inventory_lots` (new or extend `component_lots`)
  - id INTEGER PK
  - component_type TEXT CHECK('bullet'|'powder'|'case'|'primer')
  - component_id INTEGER NULL -- FK into bullets/powder/primers/cases
  - lot_number TEXT
  - quantity_initial INTEGER
  - quantity_remaining INTEGER
  - purchase_date TEXT
  - supplier TEXT
  - notes TEXT
  - created_date TEXT

- `measurement_sessions`
  - id INTEGER PK
  - lot_id INTEGER FK -> inventory_lots.id
  - measured_by TEXT
  - datetime TEXT
  - sample_size INTEGER
  - measured_all BOOLEAN
  - notes TEXT

- `measurement_values`
  - id INTEGER PK
  - session_id INTEGER FK -> measurement_sessions.id
  - item_index INTEGER
  - weight_grains REAL
  - length_mm REAL
  - neck_thickness_mm REAL
  - case_weight_gr REAL
  - passed_qc BOOLEAN NULL
  - notes TEXT

- `prep_sessions`
  - id INTEGER PK
  - brass_batch_id INTEGER FK -> brass_batches.id
  - method TEXT
  - anneal_date TEXT
  - trim_mm REAL
  - neck_bushing_size_inches REAL
  - neck_tension_notes TEXT
  - measured_after BOOLEAN
  - notes TEXT
  - created_date TEXT

Key algorithms & formulas
- Stats: mean, stddev (population vs sample), median, min, max.
- Outlier trimming: default remove values > 3 standard deviations from mean; configurable.
- 95% CI for mean: mean ± 1.96 * (sd/sqrt(n)) if n>1.
- Trim recommendation: recommended_trim = min(max_measured_length, saami_case_length) - trim_tolerance
- Neck tension suggestion: recommended_bushing = bullet_diameter - desired_interference; desired_interference depends on bullet type & use (e.g., 0.001"-.003" for target/long-range; 0.003-.006" for hunting). Show formula and let user adjust.

UI flows (high level)
- Add Lot Wizard: select component type -> select component (or create new) -> enter lot number & qty -> optional: add measurements now
- QC Measurement Wizard: select lot -> start session -> sequential input of measurements (or CSV import) -> live stats & outlier highlight -> finish and save
- Brass Prep Wizard: select brass batch -> input current times_fired and measurement sample -> run estimator for trim & neck bushing -> save prep session
- Inventory View: table with filters, quick actions (mark used, add measurement, edit lot)

Export/import
- CSV templates for measurement import/export. Columns: item_index, weight_grains, length_mm, neck_thickness_mm, notes

Safety & UX
- Prominent disclaimers on pressure-related advice; never auto-apply critical safety changes.
- Provide short help text for measurement technique and recommended tools.

Next steps
1. Add SQL migration to create `inventory_lots`, `measurement_sessions`, `measurement_values`, `prep_sessions`.
2. Implement backend CRUD and small UI wizards for bullets first.
3. Add CSV import and tests.

References
- QuickLoad/GRT manuals (conceptual)
- Basic statistics references for mean/SD/CI

