# Load Module Finish TODO

## Status

- Updated: 2026-04-13
- Scope: locked finish plan for the load module only
- Rule: follow this list in order unless explicitly replaced

## Purpose

This document exists to finish the load module without drifting into side features.

It is stricter than the broader roadmap documents.

Use it as the operational checklist for the remaining work required to make the load module coherent, explainable, robust, and sale-ready.

## Locked Intent

The load module is finished when it behaves like one technically credible product surface, not several adjacent tools.

The work in this document must stay aligned with these intentions:

1. One canonical runtime and engine path must win over parallel legacy paths.
2. Measured, modeled, derived, and recommended must stay clearly separated.
3. The module must prefer insufficient evidence over false certainty.
4. Pipe, barrel configuration, component, and lot context must stay consistent end to end.
5. The module must become stable and commercially supportable, not only feature-rich.

## Do Not Build During This Block

These are explicitly out of scope until this TODO is complete:

1. New non-core dashboards.
2. New AI or network-backed recommendation features.
3. Decorative UI redesign that does not reduce workflow friction.
4. New side modules that do not strengthen the load core.
5. Extra analytics that are interesting but not required for load-core trust.
6. Broad work on unrelated modules unless they block the load module directly.

## Definition Of Finished

The load module is not finished until all of the following are true:

1. Builder, workflow, runtime, batch, chrono, and target consume one consistent truth model.
2. All critical advice carries evidence quality, confidence, uncertainty, and blockers.
3. Rifle, barrel, barrel configuration, component, and lot context are not mixed incorrectly.
4. The system can rank robust candidates above lucky single results.
5. The next recommended test is explainable and context-aware.
6. The core commercial path works repeatedly without hidden context surprises.
7. The remaining legacy load paths are either aligned, isolated, or retired.

## Execution Order

Do not reorder these blocks without an explicit decision.

1. Canonical truth path
2. Engine input completion
3. Evidence weighting and scientific core
4. Local learning core
5. Recommendation and robustness completion
6. Consumer migration and deduplication
7. End-to-end hardening and sale-readiness

## Block 1: Canonical Truth Path

Goal: remove ambiguity about where active load state and recommendation truth live.

- [x] Verify that `load_development_sessions` plus runtime service are the canonical active-load truth.
      Done 2026-04-19: `build_load_session_runtime` is the single runtime builder. All critical
      identity reads (rifle_id, session_id, barrel_configuration_id) flow through it.
- [x] Audit builder, workflow, batch, chrono, and target entry points for competing active-state reads.
      Done 2026-04-19: All consumers use `build_active_workflow_context_from_settings(settings, db)`
      which calls `enrich_workflow_context_from_session` → `build_load_session_runtime`.
      Minor: modern_load_builder reads `usage_profile`/`target_es` from settings as
      non-critical display fallbacks — acceptable.
- [x] Replace remaining ad hoc active-context assembly with runtime-derived context where possible.
      Done 2026-04-19: No ad hoc competing active-state assembly found for critical fields.
      The workflow write path (`store_active_workflow_context`) stores only IDs/names.
      All read paths enrich from DB.
- [x] Ensure resume paths always restore canonical rifle, barrel, barrel configuration, and load session identity.
      Done 2026-04-19: Settings store IDs → `enrich_workflow_context_from_session` rebuilds
      full context from DB on every read. Context cannot drift beyond what's in the DB.
- [ ] Ensure UI labels and payloads expose the active barrel configuration everywhere critical advice is shown.
      (requires manual UI inspection — deferred to Block 7 release-readiness checklist)
- [x] Record which load-module code paths are canonical, compatibility-only, or pending retirement.
      Done 2026-04-19: Canonical: `build_load_session_runtime`, `build_active_workflow_context_from_settings`,
      `batch_workspace._get_batch_engine_result`, `smart_ammo_engine.build_smart_ammo_engine`.
      Compatibility/blocked: 4 internal builder functions (`build_evidence_recommendation_baseline`,
      `build_recommendation_control_state`, `summarize_recommendation_evidence_basis`,
      `summarize_charge_promotion_candidate`) — overlapping engine output, blocked pending
      builder-class test harness. No paths identified for immediate retirement.

Exit criteria:

1. One active load session produces one consistent context across all load-core surfaces.
2. No critical load advice depends on hidden UI state when canonical runtime state is available.

## Block 2: Engine Input Completion

Goal: complete the canonical smart-engine input so the engine is always evaluating the right context.

- [x] Resolve active component context fully from canonical session/runtime data.
      Done 2026-04-19: `_normalize_component_context` resolves ID from row OR selection,
      labels each component, status = known/partial/unresolved.
- [x] Resolve active lot context fully, including tolerant handling of partial lot selection.
      Done 2026-04-19: `_normalize_lot_context` handles None lots, partial selection,
      drift/watch flags. status = known/watch/unresolved.
- [x] Resolve environment context fully, including temperature and density-altitude-ready shape.
      Done 2026-04-19: fixed `or`-chain bug that silently dropped altitude_m=0.0.
      All 4 env fields use explicit `is None` check. Density altitude computed when all present.
- [x] Resolve measured evidence context fully from chrono, target, batch, and pressure sources.
      Done 2026-04-19: `_resolve_evidence_context` collects from chrono_imports,
      test_results, ladder_tests, batch_projects, batch_sessions, shooting_sessions,
      pressure_signs. All sources feed evidence.summary.
- [x] Ensure barrel-configuration-sensitive evidence remains conservative when older rows lack explicit setup identity.
      Done 2026-04-19: added `setup_matched_session_count` and `setup_unmatched_session_count`
      to evidence summary. NULL barrel_config on batch sessions = conservative match
      (assumed same setup). Explicit mismatch counted separately.
- [x] Add focused tests for component, lot, environment, and measured evidence resolution.
      Done 2026-04-19: 25 tests in `tests/test_engine_input_resolution.py` — all passing.

Exit criteria:

1. The engine can always state which rifle, barrel, setup, component, lot, and evidence context it is using.
2. Missing input fields degrade gracefully instead of silently shifting context.

## Block 3: Evidence Weighting And Scientific Core

Goal: make the module scientifically conservative and consistent instead of merely feature-rich.

- [x] Reuse and normalize evidence-quality logic across builder, workflow, runtime, and engine outputs.
      Done 2026-04-19: `evidence_quality_service.py` is the single source of truth for thresholds,
      signal hints, and score_to_level. All consumers import from it.
- [x] Add matched-versus-unmatched evidence scoring to engine output.
      Done 2026-04-19: `setup_matched_session_count` + `setup_unmatched_session_count` added to
      evidence summary. Engine uses matched count for `repeat_confirmed`; unmatched sessions
      appear in `evidence_diagnostics.items` and `candidate_profile.setup_unmatched_session_count`.
- [x] Add cold-bore evidence as its own first-class channel.
      Done: cold-bore channel in `_build_evidence_weighting` — status/summary, feeds hunting
      routing and `evidence_diagnostics.focus_areas`.
- [x] Add group-pattern confidence and mixed-signal handling.
      Done: `group_pattern_channel` and `mixed_signal` block in `_build_evidence_weighting`.
      Ambiguous signals cap evidence at "moderate"; mixed signal → repeat before ranking.
- [x] Ensure the engine prefers `insufficient evidence` over forced diagnosis.
      Done: `evidence_gated` blocks candidate ranking for `insufficient_evidence` and
      `pressure_or_ammo` signals. Safety block always wins.
- [x] Standardize payload/UI language for `measured`, `modeled`, `derived`, and `recommended`.
      Done: engine output consistently uses `evidence_diagnostics`, `candidate_profile`,
      `baseline_control`, `decisions.next_test`, `decisions.guidance` — all labeled.
- [x] Standardize confidence, uncertainty, blocker, and weakest-link reporting.
      Done: `decisions.recommendation_confidence` carries level/uncertainty/basis;
      `decisions.blocked_by` carries block reasons; `learning_summary.weakest_link` present.
- [x] Add targeted tests for weak evidence, mixed evidence, and blocker-driven downscoping.
      Done 2026-04-19: 18 tests in `tests/test_engine_block3_evidence.py` — all passing.

Exit criteria:

1. All critical advice explains data quality and uncertainty in a consistent way.
2. The module never looks more certain than the evidence justifies.

## Block 4: Local Learning Core

Goal: make the system genuinely learn from repeated use in the correct weapon/setup context.

- [x] Define one learning payload for rifle, barrel, and barrel configuration.
- [x] Define stable charge-window learning. (persisted in runtime service)
- [x] Define stable seating-window learning. (persisted from recommendation model)
- [x] Define lot-drift memory for bullet, powder, primer, and case contexts.
- [x] Define confirmed-candidate memory. (`confirm_load_candidate` in session service)
- [x] Define rejected-candidate memory. (`reject_load_candidate` in session service)
- [x] Persist model status as `raw`, `partially_calibrated`, or `well_calibrated`.
      Done 2026-04-16: `_normalize_learning_state` schema + `refresh_load_session_measurement_summary`
      + `_build_learning_aggregate` all verified. `model_status` survives re-open.
- [x] Ensure chrono, target, batch, and calibration series update the same learning structures.
      Done 2026-04-20: target_analyzer.py:717-721 calls `refresh_load_session_measurement_summary`
      after saving target results — verified aligned with chrono and batch. "Calibration series"
      in the MLB is scope/turret calibration stored in barrel profiles via `_save_rifle_profile_details`;
      it is not a load evidence source and correctly does not update load session learning.
- [x] Add deterministic tests for learning updates and model-status transitions.
      31 tests in `test_load_module_defensive_inputs.py`, 3 E2E tests in
      `test_load_module_e2e_core_workflow.py`.

Exit criteria:

1. The module can explain what it has learned about the selected rifle/barrel/setup.
2. Learning updates are deterministic and traceable.

## Block 5: Recommendation And Robustness Completion

Goal: finish the parts that turn analysis into practical guidance.

- [x] Finalize candidate ranking so robustness beats lucky one-off performance.
      Done 2026-04-19: single session capped at "moderate"; pressure_or_ammo always "low";
      `repeat_session_count` / `repeat_confirmed` added to `candidate_profile`.
- [x] Finalize `best next test` ordering for hunting, competition, and learning/hobby intents.
      Done 2026-04-19: hunting→`cold_bore_field_validation`; competition+no-repeats→
      `repeatability_string`; competition+repeats→`confirm_node_window`. Full map entries added.
- [x] Finalize `do not change yet` and validation-gate logic from the canonical engine output.
      Done 2026-04-19: thin/very_thin evidence adds "do not promote" guardrail;
      validation_gate status "blocked" on safety warning.
- [x] Ensure safety and evidence blockers override optimization logic.
      Done 2026-04-19: safety block always overrides usage_goal routing; pressure signal
      forces "low" robustness regardless of session count.
- [ ] Surface the active setup and confidence basis in recommendation payloads and UI text.
      (engine payload contains the data; UI wiring deferred to Block 7 hardening)
- [x] Add tests for recommendation ordering, blocked decisions, and robustness precedence.
      Done 2026-04-19: 15 tests in `tests/test_engine_block5_robustness.py` — all passing.

Exit criteria:

1. The module can recommend the next highest-value step without hand-wavy logic.
2. Robust loads are ranked above lucky single-series results.

## Block 6: Consumer Migration And Deduplication

Goal: make the canonical engine own more of the shared load advice and reduce drift.

- [x] Let `batch_analyzer.py` consume canonical engine output where possible.
      Done 2026-04-19: `BatchAnalyzer` accepts `engine_result` param; `recommendation_stack`
      items prepend `next_steps`; `next_test.recommended_action` sets `next_focus`.
      `batch_workspace.py` passes engine result in both `recompute_batch_analysis_from_db`
      and `refresh_analysis`. 8 new tests in `test_batch_analyzer_engine_integration.py`.
- [x] Audit builder, runtime, workflow, and workspace for duplicated recommendation logic.
      Done 2026-04-19. Findings:
      - `digital_twin.py`: already fully engine-aware — uses `build_engine_result_from_input` directly.
      - `build_learning_workflow_guidance` (MLB L411): already reads `smart_engine.engine_result` — not duplicate.
      - `summarize_recommendation_return_targets` (MLB L1709): wraps engine output for UI — keep.
      - `build_evidence_recommendation_baseline` (MLB L1405): INTERNAL ONLY — overlaps engine `baseline_control`. Blocked.
      - `build_recommendation_control_state` (MLB L1523): INTERNAL ONLY — overlaps engine `baseline_control` alignment. Blocked.
      - `summarize_recommendation_evidence_basis` (MLB L1623): INTERNAL ONLY — overlaps engine `evidence_diagnostics`. Blocked.
      - `summarize_charge_promotion_candidate` (MLB L1311): INTERNAL ONLY — overlaps engine `candidate_ranking`. Blocked.
      All 4 blocked functions are consumed by the 17k-line builder class. Safe removal
      requires a builder-class test harness that does not yet exist.
- [~] Remove or isolate duplicated logic once the engine covers the same decision space.
      Done 2026-04-21: All 4 functions marked `# LEGACY-ISOLATED` in `modern_load_builder.py`.
      Full removal deferred to post-1.0 (needs builder-class test harness). Accepted as known gap.
- [x] Ensure `digital_twin.py`, builder, runtime, and workspace expose aligned engine summaries.
      `digital_twin.py` verified aligned. Builder reads engine via `build_learning_workflow_guidance`.
      Runtime service builds `smart_engine` at session load. Workspace reads it via `_get_batch_engine_result`.
- [x] Add integration tests across builder -> runtime -> workspace using the same engine truth.
      Done 2026-04-19: 6 tests in `tests/test_load_module_engine_integration.py`. Verifies
      runtime → batch workspace alignment: same engine_result, same next_focus, same
      recommendation_stack, safety propagation, and graceful no-session fallback.

Exit criteria:

1. The same load context produces the same recommendation basis across major surfaces.
2. Duplicate recommendation logic no longer competes with the engine path.

## Block 7: End-To-End Hardening And Sale-Readiness

Goal: finish the load module as a repeatable, supportable commercial core.

- [x] Make engine parsing tolerant of older JSON payloads.
- [x] Make engine and runtime tolerant of missing fields and partial legacy rows.
      Done 2026-04-16: 31 defensive-input regression tests cover malformed/partial inputs.
- [x] Ensure stale UI state cannot override newer real evidence.
      Done 2026-04-20: `modern_load_builder.py` does not cache `workflow_context` or engine
      result on `self`. All evidence-related reads call `build_active_workflow_context_from_settings`
      fresh from DB. `recommendation.active_settings` stores user-entered environment context
      (temperature, pressure) — not evidence. All three evidence sources (chrono, target, batch)
      call `refresh_load_session_measurement_summary` after saves. Known remaining gap: 4 blocked
      internal builder functions use stale recommendation state for the callout panel — isolated,
      does not affect evidence reads, blocked pending builder-class test harness.
- [x] Add regression tests for malformed and partial inputs.
      `test_load_module_defensive_inputs.py`: 31 tests.
- [x] Add end-to-end tests for the core commercial path:
      `test_load_module_e2e_core_workflow.py`: 3 tests (14 steps each), covers:
- [x] Create/select rifle and active barrel configuration.
- [x] Start guided load session.
- [~] Move into builder. (builder not covered by E2E tests — deferred to post-1.0, needs builder-class test harness)
- [x] Log chrono/target/batch evidence.
- [x] Resume later without context drift. (`test_context_survives_reopen_with_no_measurements`)
- [x] Review recommendation, confidence, and blockers.
- [x] Define which legacy load paths are retired, compatibility-only, or still core.
      Done 2026-04-20 (findings from Blocks 1 and 6):
      Canonical: `build_load_session_runtime`, `build_active_workflow_context_from_settings`,
      `batch_workspace._get_batch_engine_result`, `smart_ammo_engine.build_smart_ammo_engine`.
      Compatibility/blocked (not retired): 4 internal builder functions
      (`build_evidence_recommendation_baseline`, `build_recommendation_control_state`,
      `summarize_recommendation_evidence_basis`, `summarize_charge_promotion_candidate`) —
      internal to builder, overlap engine output, safe removal blocked pending builder-class
      test harness. No paths identified for immediate retirement.
- [x] Add a release-readiness checklist for the load module.
      `docs/load_module_release_readiness.md` created 2026-04-16.
- [ ] Verify the load module is stable enough for repeated real use, not only developer demos.
      Manual checklist in `docs/load_module_release_readiness.md` — NOT YET RUN.
      CI: 199 tests green (2026-04-21). Remaining gate: human manual verification only.

Exit criteria:

1. The commercial core path can be run repeatedly without hidden context drift.
2. The remaining module set is supportable and packaging-ready.

## Working Rule While Executing This TODO

Before starting any new load-module task, check it against this filter:

1. Does it strengthen the canonical truth path?
2. Does it strengthen evidence, learning, recommendation quality, or robustness?
3. Does it reduce drift, duplication, or support risk?

If the answer is no, do not build it yet.