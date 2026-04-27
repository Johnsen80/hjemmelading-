# Valkyrie Ballistics 1.0 Release Roadmap

## Purpose
Define the work needed to reach a stable, sellable 1.0 release that is modern, trustworthy, and usable by researchers, ammo developers, competition shooters, hunters, and beginners.
See [docs/platform_decisions.md](docs/platform_decisions.md) for platform and MVP scope assumptions.

## 1.0 Release Criteria (proposed)
- No visible "coming soon" or placeholder UI in core workflows.
- Modern, consistent UI system with clear information hierarchy and fast navigation.
- Persona-based modes: Beginner, Advanced, Research with tailored workflows and guardrails.
- Data credibility: provenance, calibration status, model versioning, audit trail.
- Measurable uncertainty displayed for critical results (confidence bands, assumptions).
- Performance targets met for large datasets and heavy charts (no lag spikes).
- Windows installer stable and repeatable, with update process defined.
- Internationalization-ready UI with user-selectable languages, including Norwegian.
- User documentation, onboarding, and safety disclaimers complete.
- Legal and support readiness: EULA, privacy, support workflow, and version policy.

## Personas and outcomes
- Researchers: reproducible experiments, traceability, and exportable reports.
- Ammo developers: batch QC, repeatable processes, and comparison tools.
- Competition shooters: fast iteration, optimization tools, and clear insights.
- Hunters: simple workflows, practical recommendations, and offline reliability.
- Beginners: guided steps, safe defaults, and explainable results.

## Phases and scope

### Phase 1 - Modern UI foundation
- Finalize design system (typography, colors, spacing, components).
- Create design system brief and tokens (docs/design_system_brief.md).
- Replace placeholders in analysis statistics (trends, cost, comparisons, most used).
- Establish navigation patterns for persona modes.
- Accessibility and readability pass (contrast, sizing, density).

Acceptance:
- Core UI screens use the design system components.
- No placeholders remain in production UI.
- At least 3 end-to-end user flows are modernized.

Selected Phase 1 workflows (initial):
- Chronograph import -> validation -> analysis charts -> save session.
- Load development workflow -> comparison -> recommendation notes -> export report.
- Manual/CSV entry -> analysis statistics -> report/export.

### Phase 2 - Persona modes and onboarding
- Implement Beginner / Advanced / Research modes.
- Contextual help and safety hints per mode.
- First-run onboarding with sample data and guidance.

Acceptance:
- Mode switch changes visible UI and workflow complexity.
- Beginner flow covers data entry -> analysis -> report.

### Phase 3 - Data integrity and credibility
- Harden ingest validation (CSV mapping, unit checks, range checks).
- Add audit trail for critical operations.
- Add uncertainty/assumptions panels for key outputs.
- Model calibration process and benchmark reports.

Acceptance:
- Every analysis result can be traced to input data + model version.
- Calibration status is shown in UI.

### Phase 4 - Performance and reliability
- Profiling on large datasets and heavy chart interactions.
- Fix slow paths and memory spikes.
- Expand Windows GUI smoke and regression tests.

Acceptance:
- Large datasets remain responsive during navigation and plotting.
- Automated GUI smoke runs on Windows with repeatable results.

### Phase 5 - Reporting, packaging, and commercial readiness
- Report templates with metadata and reproducibility summary.
- Export pipeline (PDF/HTML/CSV) with audit data.
- Signed installer and versioned release process.
- User docs, EULA, privacy, and support workflow.

Acceptance:
- Reports contain model version, data timestamp, and calibration status.
- Installer passes clean install, update, and uninstall tests.

## Definition of done by area
- UI: Modern visuals, consistent layout, and no legacy placeholders.
- UX: Clear mode separation and guided beginner flow.
- Credibility: Audit trail, provenance, and uncertainty shown.
- QA: Automated smoke + regression in CI, manual checklist for releases.
- Docs: Quick start, user guide, and safety disclaimers.
- Legal: EULA, privacy policy, and support policy finalized.

## Risks and mitigations
- Risk: scope creep in UI redesign.
  - Mitigation: lock the design system and only expand after 1.0.
- Risk: performance regressions after UI upgrades.
  - Mitigation: baseline performance tests and profiling for each release.
- Risk: trust gaps without calibration data.
  - Mitigation: show calibration status and data quality explicitly.

## Evidence and verification
- CI: lint, type check, headless tests.
- Windows GUI smoke test results archived per release.
- Benchmark reports for performance and model accuracy.

## Next actions
- Review and lock the design system brief (colors, typography, components).
- Validate the Phase 1 workflows and adjust if needed.
- Define the calibration dataset(s) and expected accuracy thresholds.
