# Local Smart Ammo Engine Execution Plan

## Status

- Updated: 2026-04-12
- Scope: canonical execution plan for the local smart ammo engine
- Priority: locked until explicitly replaced

## Locked Direction

This plan is locked to the following direction:

- one local, offline-first smart ammo engine
- no external AI in the core recommendation path
- one canonical internal engine result
- one learning loop per weapon, barrel, configuration, load and lot context
- UI and workflow surfaces must consume engine output, not invent parallel domain logic

## Hard Rules

These rules are not optional during this block.

1. The engine must be explainable from internal logic.
2. The engine must prefer measured evidence over generic reference data when evidence quality is sufficient.
3. The engine must not present shooter diagnosis as fact.
4. The engine must rank robust candidates above lucky single-series results.
5. Harmonic node logic and seating/jump logic are core engine logic, not side calculations.
6. Existing modules must be reused where possible; new work should primarily connect and normalize.
7. UI work must follow engine consolidation, not replace it.
8. The program must become production-stable and sale-ready, not only technically interesting.
9. Old or redundant code paths that do not support the target product may be removed or retired.
10. Seamless operation, robustness and maintainability have equal priority with domain intelligence.

## Primary Goal

Build one canonical local engine service that can:

- resolve full rifle and component context
- score component interaction plausibility
- evaluate harmonic node strength and robustness
- evaluate seating and jump sensitivity
- interpret measured evidence conservatively
- learn from confirmed results over time
- recommend the most promising and safest next ammunition candidate or next test

This must be done in a way that supports a stable commercial product:

- low crash risk
- predictable runtime behavior
- fewer parallel legacy paths
- simpler support and verification

## What This Block Is Not

This block is not:

- a new dashboard project
- a workboard feature block
- an external AI integration
- a visual redesign sprint
- a rewrite of every existing module

It is an orchestration and normalization block.

It is also a cleanup block where legacy paths, duplicate logic and dead-end features may be removed when they weaken stability or increase maintenance cost.

## Canonical New Service

Introduce a new orchestration service:

- `src/modules/smart_ammo_engine.py`

This service should not replace all helper code.

It should:

- assemble canonical input
- call the right existing helpers
- normalize their outputs
- apply local decision rules
- emit one engine payload

## Canonical Engine Input

The engine input must always be buildable from the same shape.

### Required input groups

1. Weapon context
- weapon id
- weapon type
- action type
- magazine constraint when relevant

2. Barrel context
- barrel id
- barrel name
- caliber
- barrel length
- twist
- barrel geometry / contour
- round count if known

3. Barrel configuration context
- configuration id
- suppressor / brake / tuner state
- muzzle device weight and length if known
- support and attachment metadata

4. Chamber and seating context
- freebore
- throat measurements
- jump and jam references
- CBTO / COAL context
- bullet-specific jump history if known

5. Component context
- bullet id and bullet profile
- powder id and powder profile
- primer id and primer profile
- brass archetype and brass batch

6. Lot context
- active bullet lot
- active powder lot
- active primer lot
- active brass lot

7. Environment context
- temperature
- pressure
- humidity
- altitude / density altitude where available

8. Measured evidence
- chrono history
- group history
- target pattern history
- cold-bore evidence
- POI drift evidence
- pressure signs

9. Learning context
- confirmed nodes
- rejected candidates
- stable seating ranges
- stable velocity windows
- lot sensitivity history

## Canonical Engine Output

The engine output must be structured and reusable by all major surfaces.

### Required output groups

1. Identity
- rifle / barrel / configuration identity
- ammo profile identity
- active lot identity

2. Safety
- safety state
- pressure state
- blocked actions

3. Physics
- predicted pressure summary
- internal ballistics summary
- component interaction summary
- environment sensitivity summary

4. Harmonics
- node bands
- node width
- node robustness
- timing suspicion / confidence
- change sensitivity

5. Seating and jump
- current jump state
- seating sensitivity
- seating recommendation band
- whether seating is more appropriate than powder change

6. Evidence
- evidence quality
- evidence gaps
- matched vs unmatched evidence
- confidence and uncertainty

7. Learning
- rifle-specific preferences
- learned stable regions
- lot-sensitivity notes
- confirmation memory

8. Decisions
- best candidate group
- next recommended test
- validation gate
- execution protocol
- what should not be changed yet
- candidate ranking
- explainable reasons

## Build Sequence

## Block 1: Canonical input resolver

### Goal

Build a single input resolver for the engine.

### Deliverables

- normalize weapon, barrel and barrel-configuration context
- normalize active component and lot context
- normalize environment context
- normalize measured evidence references

### Reuse first

- `barrel_configuration.py`
- `ammo_profile_manager.py`
- `reference_owned_data_service.py`
- `load_session_runtime_service.py`
- `weapon_learning_domain_model.md`

### Exit condition

One helper can return a canonical engine input payload from an active load session or batch-linked session context.

## Block 2: Harmonization of component and physics logic

### Goal

Connect the already-existing physics pieces into one consistent engine pass.

### Deliverables

- bullet fit and twist fit summary
- powder plausibility and charge-window summary
- brass and case-capacity confidence summary
- primer sensitivity summary
- internal ballistics summary
- pressure guard summary

### Reuse first

- `reference_owned_data_service.py`
- `internal_ballistics.py`
- `pressure_calculator.py`
- `modern_load_builder.py`
- `digital_twin.py`

### Exit condition

The engine can explain why the current recipe is plausible, fragile, conservative or blocked.

### Current delivered in this block

- canonical `bullet_fit` output wired from existing bullet geometry / twist / stability helpers
- canonical `chamber_jump` output wired from seating-depth profiles, jump measurements and best known seating evidence
- runtime, builder, workspace and digital twin now surface the same bullet-fit and jump truth from the engine

## Block 3: Harmonic node and seating engine

### Goal

Make harmonics and seating first-class engine outputs.

### Deliverables

- normalized harmonic node summary
- broad node vs narrow node evaluation
- seating/jump interaction summary
- timing suspicion summary
- robust node confidence
- when to change seating before powder

### Reuse first

- `rifle_harmonics.py`
- `digital_twin.py`
- seating and jump utilities in `modern_load_builder.py`
- `batch_analyzer.py`

### Exit condition

The engine can rank “stay in node”, “adjust seating”, “adjust charge”, or “stop and verify” with reasons.

## Block 4: Evidence normalization and weighting

### Goal

Make the engine consistent about what counts as strong evidence.

### Deliverables

- evidence-weight model
- matched evidence scoring
- cold-bore handling
- session quality flags
- pattern confidence
- conservative mixed-signal handling

### Reuse first

- `batch_analyzer.py`
- `load_session_runtime_service.py`
- `batch_workspace.py`
- `reference_owned_data_service.py`

### Exit condition

The engine can say not only what it thinks, but how strongly the evidence deserves trust.

## Block 5: Rifle-specific local learning

### Goal

Persist local internal learning without external AI.

### Deliverables

- learned stable charge windows
- learned stable seating windows
- lot drift memory
- rifle/barrel/configuration memory
- confirmation history and rejection history

### Notes

This should be explicit and explainable.

It should store:

- what was tried
- what was confirmed
- what drifted
- what remained robust

### Exit condition

The engine gets measurably better for the same rifle over time.

## Block 6: Candidate generator and next-test planner

### Goal

Produce smart, local recommendations before the user wastes rounds.

### Deliverables

- next candidate combinations
- next test ordering
- do-not-change-yet rules
- stop conditions
- final recommendation confidence

### Exit condition

The engine can generate the best next test path, not just analyze old results.

## Block 7: Consumer migration

### Goal

Make major UI surfaces consume engine output instead of parallel local logic.

### Target consumers

- `modern_load_builder.py`
- `batch_analyzer.py`
- `batch_workspace.py`
- `load_session_runtime_service.py`
- `digital_twin.py`

### Exit condition

The app behaves like one smart system with many views, not many smart views with competing logic.

## Robustness Checklist

The block is not complete before these hold:

- engine handles missing rifle fields
- engine handles missing lot fields
- engine handles older JSON payloads
- engine handles stale `QSettings`
- engine emits confidence and uncertainty for important decisions
- engine emits “insufficient evidence” instead of inventing certainty
- no engine-critical path depends on network or external model calls
- major user flows are deterministic and testable
- legacy code that competes with the canonical engine path is either removed, isolated or clearly marked as non-core
- no important recommendation depends on hidden UI-local state
- the module set is maintainable enough for support, packaging and commercial delivery

## Cleanup Rule

Cleanup is allowed and encouraged when it improves:

- stability
- readability
- testability
- supportability
- commercial readiness

Examples of acceptable cleanup:

- remove duplicate recommendation paths
- retire dead legacy screens that are no longer part of the target load flow
- collapse overlapping helper layers
- stop carrying historical “fun” features that distract from the core product and add drift risk

The cleanup rule does not mean reckless deletion.

It means that non-core features should not be allowed to weaken the sale-ready product.

## Release Gate For This Plan

This plan is only complete when the engine can do all of the following:

1. Read a real rifle and configuration context correctly.
2. Read real component and lot context correctly.
3. Combine harmonics, seating, pressure and evidence into one recommendation.
4. Learn locally from confirmed outcomes.
5. Produce a ranked next action with confidence and blockers.
6. Feed the same core result to builder, runtime and workspace.
7. Run through the core load-development flow without obvious friction, broken handoffs or legacy detours.
8. Be stable enough that the product can be used as a commercial tool, not just an internal prototype.
