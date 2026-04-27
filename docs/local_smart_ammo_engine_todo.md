# Local Smart Ammo Engine TODO

## Status

- Updated: 2026-04-12
- Scope: locked operational TODO for the local smart ammo engine
- Rule: this list is the current execution order until explicitly replaced

## Locked Priorities

Do not reorder these without an explicit decision.

1. canonical engine input
2. harmonics and seating core
3. component interaction core
4. evidence weighting
5. local learning
6. candidate generation
7. consumer migration
8. stability, cleanup and sale-readiness

## Phase 1: Canonical Engine Input

- [x] Create `src/modules/smart_ammo_engine.py`
- [x] Add canonical engine build entry points
- [x] Resolve weapon context from existing rifle profile sources
- [x] Resolve active barrel context
- [x] Resolve active barrel configuration context
- [x] Resolve chamber and jump context
- [x] Resolve active component context
- [x] Resolve active lot context
- [x] Resolve environment context
- [x] Resolve measured evidence context
- [x] Normalize input into one predictable payload shape
- [x] Add focused tests for canonical input resolution

## Phase 2: Harmonics and Seating Core

- [x] Reuse `rifle_harmonics.py` as the primary harmonics source
- [x] Normalize harmonic node bands into engine output
- [ ] Add broad-node vs narrow-node interpretation
- [x] Add harmonic robustness summary
- [x] Add timing suspicion summary from measured patterns
- [x] Add explicit seating/jump section in engine output
- [x] Reuse existing seating and jump helpers from builder/ballistics logic
- [x] Add “change seating before powder” decision rule where supported
- [x] Add tests for node width, robustness and seating-first decisions

## Phase 3: Component Interaction Core

- [x] Normalize bullet fit and twist fit into engine output
- [x] Normalize powder suitability / charge plausibility into engine output
- [x] Normalize primer influence / pressure sensitivity into engine output
- [x] Normalize brass and case-capacity confidence into engine output
- [x] Normalize lot summaries into engine output
- [x] Reuse `internal_ballistics.py` and `pressure_calculator.py`
- [x] Reuse `reference_owned_data_service.py` trust and lot summaries
- [x] Add tests for lot-aware and component-aware output

## Phase 4: Evidence Weighting

- [ ] Reuse `batch_analyzer.py` evidence quality model where possible
- [ ] Normalize matched vs unmatched evidence scoring
- [ ] Add cold-bore evidence channel
- [ ] Add group-pattern confidence channel
- [ ] Add mixed-signal handling rule
- [ ] Ensure the engine prefers “insufficient evidence” over forced conclusions
- [ ] Add tests for evidence weighting and mixed signals

## Phase 5: Local Learning

- [ ] Define local learning payload for rifle/barrel/configuration
- [ ] Define stable charge-window learning
- [ ] Define stable seating-window learning
- [ ] Define lot-drift memory
- [ ] Define confirmed candidate memory
- [ ] Define rejected candidate memory
- [ ] Store learning locally without external AI
- [ ] Add tests for deterministic learning updates

## Phase 6: Candidate Generator

- [x] Add candidate ranking based on safety + node + evidence + learning
- [x] Add “best next test” output
- [x] Add “do not change yet” output
- [x] Add “blocked by safety / evidence / configuration” output
- [x] Add confidence and uncertainty to recommendations
- [ ] Add tests for recommendation ordering

## Phase 7: Consumer Migration

- [x] Let `digital_twin.py` consume canonical engine output
- [x] Let `modern_load_builder.py` consume canonical engine output
- [x] Let `load_session_runtime_service.py` consume canonical engine output
- [ ] Let `batch_analyzer.py` consume canonical engine output where possible
- [x] Let `batch_workspace.py` consume canonical engine output where possible
- [ ] Remove duplicated recommendation logic where the engine can own it
- [ ] Add integration tests across builder -> runtime -> workspace

## Phase 8: Robustness and Drift Safety

- [ ] Make engine parsing tolerant of older JSON payloads
- [ ] Make engine tolerant of missing fields
- [ ] Make engine tolerant of incomplete lot data
- [ ] Make engine tolerant of incomplete barrel/profile data
- [ ] Ensure stale UI state cannot override real evidence
- [ ] Ensure all critical advice carries blockers and uncertainty
- [ ] Add regression tests for malformed or partial inputs

## Phase 9: Stability, Cleanup and Sale-Readiness

- [ ] Identify legacy or duplicate load-development paths that compete with the canonical engine path
- [ ] Mark which old modules are core, compatibility-only, or candidates for retirement
- [ ] Remove or isolate redundant recommendation logic that weakens maintainability
- [ ] Remove or retire non-core “fun” features if they increase drift or support cost
- [ ] Simplify critical code paths so the core product is easier to verify and support
- [ ] Ensure core user flow works without hidden context surprises or broken handoffs
- [ ] Add end-to-end tests for the core commercial path
- [ ] Add a release-readiness checklist for the load-engine module
- [ ] Verify that the module is stable enough for repeated real use, not only developer demos
- [ ] Verify that the module set is clean enough to package and support as a saleable product

## Out Of Scope For This Locked Block

Do not let these take over the block:

- [ ] external AI integration
- [ ] network-backed recommendation logic
- [ ] major dashboard redesign
- [ ] workboard-only feature expansion
- [ ] decorative UI polish without engine value

## Definition Of Done

This TODO is only complete when:

- [ ] one canonical engine service exists
- [ ] harmonics and seating are first-class outputs
- [ ] component interaction is first-class output
- [ ] local learning updates deterministically
- [ ] recommendation output is ranked and explainable
- [ ] builder, runtime and workspace consume the same core engine result
- [ ] the engine is offline-first and external-AI-free
- [ ] the core module path is stable, cleaned up and commercially supportable

## Current Engine Additions

- [x] Canonical `guidance` output is present
- [x] Canonical `validation_gate` output is present
- [x] Canonical `execution_plan` output is present
- [x] Canonical `do_not_change_yet` output is present
- [x] Canonical `blocked_by` output is present
- [x] Canonical `recommendation_confidence` output is present
- [x] Canonical `baseline_control` output is present
- [x] Runtime delta exposes engine gate and protocol summaries
- [x] Builder guidance surfaces engine gate and protocol summaries
- [x] Batch workspace summaries surface engine gate and protocol summaries
- [x] Canonical `bullet_fit` output is present
- [x] Canonical `chamber_jump` output is present
- [x] Runtime delta exposes engine bullet-fit and jump summaries
- [x] Builder guidance surfaces engine bullet-fit and jump summaries
- [x] Batch workspace summaries surface engine bullet-fit and jump summaries
