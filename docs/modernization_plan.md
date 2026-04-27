# Valkyrie Ballistics - Modernization Plan v1

## Vision
Build the most capable reloading and ballistics platform for shooters, reloaders, and ammo manufacturers. The product must feel like a modern lab console: fast, precise, and trustworthy.

## Decision log
See [docs/platform_decisions.md](docs/platform_decisions.md) for platform, offline-first, and MVP scope decisions.

## Product pillars
- Depth without friction: beginner friendly but never limiting for advanced users.
- Reproducible science: experiments, metadata, and audit trails are first class.
- Precision at scale: handles large datasets and dense charts without lag.
- Hybrid by default: offline first with optional cloud sync and collaboration.
- Unique identity: a visual system that is unmistakably Valkyrie.
- Owned intelligence: the core motor is local, weapon-specific, and not dependent on external AI services.

## Personas and modes
- Beginner mode: guided workflows, safe defaults, and structured steps.
- Advanced mode: full control, batch operations, power tools.
- Research mode: experiment management, parameter sweeps, and traceability.

## Information architecture
- Workspace: projects, revisions, roles, experiment timeline.
- Data: manual entry, CSV import, image ingest, device hub, calibration.
- Analyze: QC, outliers, drift, batch comparisons, stats.
- Simulate: ballistics engine, weather, terrain, scenario compare.
- Develop: load development, optimization, design of experiments.
- Reports: templates, exports, compliance, reproducibility.

## Core layout
- Top bar: project selector, command palette, mode switch, sync status.
- Left nav: primary domains, pinned workflows, recent items.
- Main canvas: charts, maps, tables, experiment timeline.
- Right inspector: parameters, AI insights, warnings, and notes.

## Data ingest platform
- Manual data entry with smart defaults and unit awareness.
- CSV import with field mapping and data validation.
- Image ingest for target groups and chronograph screens.
- Device hub for sensor integration and calibration profiles.

## Charting and performance
- Multi-axis plots, overlay comparisons, confidence intervals.
- Progressive rendering with LOD/decimation.
- Cached statistics and async computations.
- Report ready exports with embedded metadata.

## Local learning motor roadmap
Phase 0 - Instrumentation and truth model
- Standardized metadata on all events and measurements.
- Explicit split between measured, modeled, derived, and recommended values.

Phase 1 - QC and anomaly detection
- Outlier detection, drift monitoring, variance alerts.
- Input-quality gating before strong recommendations are shown.

Phase 2 - Calibration and prediction
- Predictive models with uncertainty scores and suggestions.
- Local calibration per weapon, barrel, component context, and lot history.

Phase 3 - Evidence-driven research assistant
- Experiment design suggestions and auto-report generation.
- All guidance remains local, traceable, and explainable without remote AI.

## Phase 2/3 scope

### Phase 2 - Prediction and guidance scope
- Predict velocity, pressure, ES/SD, and group size with uncertainty bands.
- Temperature sensitivity and drift predictors tied to ammo profiles.
- Guidance engine that suggests next test points (charge, seating, temp) with safety limits.
- Model calibration per rifle/ammo profile with versioned metadata and confidence.
- UI surfaces: guidance panel in Develop, prediction overlays in Analyze, and rationale text.
- Data prerequisites: minimum sample thresholds and data quality checks before scoring.
- Safety guardrails: hard caps on pressure, manual confirmations, and explicit disclaimers.
- Out of scope: fully automated load generation, cloud training, remote LLM guidance, multi-user collaboration.

### Phase 3 - Research assistant scope
- Experiment design (DOE templates and adaptive sampling) with step-by-step plans.
- Auto-report generation (PDF/HTML) with full metadata and audit trails.
- Cross-run synthesis: trend narratives, anomalies, and lessons learned.
- Assistant UI: research queue, hypothesis tracking, and action checklists.
- Optional collaboration hooks (commenting and shareable experiment packs) when cloud is enabled.
- Out of scope: external answers without local data context, automated safety-critical decisions, OpenAI-dependent product logic.

## Hybrid architecture
- Local encrypted storage and offline first workflows.
- Optional cloud sync for collaboration and heavy training.
- Terrain and LiDAR caches for local compute and accuracy.
- No dependency on OpenAI or external AI providers in the core product experience.

## Internationalization and localization
- User-selectable UI language; include Norwegian in 1.0.
- Externalize all UI strings with stable keys and fallback to English.
- Locale-aware formats for dates, numbers, and units.
- Support text expansion and avoid fixed-width labels.
- Version translation files and validate missing keys.

## Milestones
- M1: New shell UI and mode switcher.
- M2: Data hub and ingest pipelines.
- M3: Chart engine and performance upgrades.
- M4: Local learning baseline (QC + explain panel + calibration status).
- M5: Terrain and LiDAR integration.
- M6: Reporting system and compliance packs.

## Status (2026-03-11)
- Headless smoke checks stabilized for CI/Windows.
- Packaging specs made portable with PyQt6 resource collection.
- Settings/mode manager and safe logging hardened.
- UI placeholders remain listed in under_utvikling_liste.md.

## Success metrics
- Time to first analysis under 5 minutes for beginners.
- Stable 60 fps chart interaction on 1M+ data points.
- Reproducible reports with full metadata in one click.
