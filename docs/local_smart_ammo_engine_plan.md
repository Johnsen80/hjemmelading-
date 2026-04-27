# Local Smart Ammo Engine Plan

## Purpose

This document describes how to turn the current codebase into the product direction the project actually wants:

- one local, offline-first smart ammo engine
- self-learning from internal data only
- no external AI dependency
- rifle-specific, setup-specific, lot-aware recommendations
- robust node finding and safer decision support

The main goal is not to create more separate modules.

The main goal is to connect the modules that already exist into one explainable engine.

## Product Rule

The program must not depend on external AI to understand or recommend ammunition.

It must become smart through:

- internal physics
- structured component data
- rifle and barrel profiles
- measured evidence
- lot and profile learning
- conservative decision rules

## What Already Exists

The codebase already contains strong building blocks.

### 1. Rifle and barrel profile layer

Relevant files:

- `src/modules/rifle_profile_editor.py`
- `src/modules/rifle_database_manager.py`
- `src/utils/barrel_configuration.py`
- `src/utils/rifle_harmonics.py`

What already exists:

- weapon platform and barrel concepts
- active barrel and barrel configuration resolution
- chamber and jump-related profile fields
- muzzle-device/configuration support
- harmonics-related barrel metadata
- bullet profile linkage per barrel

Important conclusion:

The project already has the beginnings of the correct domain center:
weapon -> barrel -> barrel configuration.

### 2. Component and lot layer

Relevant files:

- `src/modules/ammo_profile_manager.py`
- `src/modules/component_lot_tracker.py`
- `src/modules/reference_owned_data_service.py`
- `src/tools/components_catalog_service.py`

What already exists:

- ammo profiles with rifle, bullet, powder, primer, case, COAL, CBTO, velocity and BC
- lot tracking for bullet, powder, primer and brass
- lot quality summaries and trust summaries
- evidence summaries per load/profile

Important conclusion:

The project already has most of the raw data needed to become lot-aware and component-aware.
The weak point is not missing data structures. The weak point is that the recommendation logic is not yet driven by one combined engine.

### 3. Physics and simulation layer

Relevant files:

- `src/modules/digital_twin.py`
- `src/utils/rifle_harmonics.py`
- `src/utils/internal_ballistics.py`
- `src/utils/pressure_calculator.py`
- `src/utils/environment.py`
- `src/utils/ballistics.py`

What already exists:

- service-backed digital twin entry point
- fallback simulation logic
- harmonics profile calculation
- internal ballistics summaries
- pressure estimation and safety checks
- environment density and altitude helpers
- jump and jam helper calculations

Important conclusion:

The project already has a real physics/tooling layer. It is not fully unified yet, but it is enough to build an internal smart engine without external AI.

### 4. Measured evidence and batch learning layer

Relevant files:

- `src/modules/batch_analyzer.py`
- `src/modules/batch_workspace.py`
- `src/tools/load_session_runtime_service.py`
- `src/modules/modern_load_builder.py`

What already exists:

- chrono and group interpretation
- spread-signal logic
- evidence-quality logic
- validation/readiness logic
- batch comparison and promotion gates
- session/workboard planning
- runtime evidence propagation

Important conclusion:

The project already has a good evidence and decision layer.
This layer should become a consumer of one smart ammo engine, not the place where the whole intelligence lives.

### 5. Learning and profile-insight layer

Relevant files:

- `src/modules/load_data_service.py`
- `src/modules/profile_insights_service.py`
- `src/modules/reference_owned_data_service.py`
- `docs/weapon_learning_domain_model.md`

What already exists:

- profile evidence summaries
- trust maps
- profile health summaries
- domain thinking that already points toward correct learning levels

Important conclusion:

The project already knows, at least conceptually, that learning should happen at the correct layer.
That is a major advantage.

## Main Gap

The main gap is not lack of modules.

The main gap is that the system is still split into smart local pieces instead of one canonical engine with one input model, one learning model, and one decision model.

Today the codebase has:

- good profile pieces
- good component pieces
- good evidence pieces
- good UI pieces
- good safety pieces

But they are not yet orchestrated as one local self-learning ammo engine.

## Correct Target Architecture

## 1. Canonical engine inputs

Create one internal engine payload that always works from the same shape:

- weapon platform context
- active barrel context
- active barrel configuration
- chamber and jump references
- ammo profile and active component selection
- active lots
- environment state
- measured evidence
- historical rifle learning

This payload should be built once and reused by:

- digital twin
- modern load builder
- batch analyzer
- batch workspace
- runtime service

## 2. Canonical engine outputs

The engine should return one structured result containing:

- safety state
- physics summary
- harmonic node summary
- seating and jump summary
- component interaction summary
- lot sensitivity summary
- evidence confidence
- rifle-learning deltas
- candidate ranking
- next recommended test
- blocked actions / guardrails

Everything else in the UI should read from this.

## 3. Internal engine layers

### Layer A: profile resolution

Responsibilities:

- resolve weapon, barrel, barrel configuration
- resolve chamber/jump context
- resolve active lots
- resolve intended use profile

Primary source candidates:

- `rifle_profile_editor.py`
- `rifle_database_manager.py`
- `barrel_configuration.py`
- `ammo_profile_manager.py`

### Layer B: component interaction model

Responsibilities:

- bullet + twist + stability fit
- powder + bullet + charge plausibility
- brass + case capacity + pressure confidence
- primer + pressure/ES sensitivity
- seating/jump sensitivity context

Primary source candidates:

- `reference_owned_data_service.py`
- `modern_load_builder.py`
- `pressure_calculator.py`
- `internal_ballistics.py`

### Layer C: harmonics and node model

Responsibilities:

- estimate robust node bands
- distinguish broad node from narrow node
- interpret vertical spread as timing evidence when supported
- connect seating-depth movement to node movement
- estimate robustness under small variation

Primary source candidates:

- `rifle_harmonics.py`
- `digital_twin.py`
- `batch_analyzer.py`

### Layer D: measured evidence model

Responsibilities:

- normalize chrono data
- normalize target/group data
- normalize pattern metrics
- track cold-bore vs general session evidence
- track matched vs unmatched evidence

Primary source candidates:

- `load_session_runtime_service.py`
- `batch_analyzer.py`
- `batch_workspace.py`

### Layer E: rifle-specific learning

Responsibilities:

- learn what this rifle/barrel/configuration likes
- learn stable charge windows
- learn stable seating windows
- learn lot sensitivity
- learn which candidates stayed robust after confirmation

This should remain local and explainable.

It should be based on:

- weighted historical evidence
- confirmation status
- robustness, not only best single group

### Layer F: decision and planning

Responsibilities:

- rank next candidates
- decide whether to change charge, seating, lot, or stop
- choose next test type
- refuse premature promotion

Primary source candidates:

- `batch_analyzer.py`
- `batch_workspace.py`
- `modern_load_builder.py`

## What Should Be Reused, Not Rebuilt

The following should be reused aggressively:

- barrel hierarchy and configuration logic
- lot tracking
- profile evidence/trust summaries
- harmonics helpers
- pressure and internal-ballistics helpers
- batch evidence logic
- runtime session summary plumbing

The project does not need more isolated modules first.

It needs one new orchestration service.

## Recommended New Core Service

Introduce one new internal service, for example:

- `src/modules/smart_ammo_engine.py`

Suggested responsibilities:

- build canonical engine input
- call existing helpers in the right order
- merge outputs into one structured result
- store learning deltas for rifle/barrel/configuration
- expose one engine result to UI and workflow surfaces

Important:

This service should not become a giant physics file.

It should orchestrate specialized helpers that already exist.

## Build Order

### Block 1: canonical engine input and output

Build first:

- canonical input schema
- canonical output schema
- profile/component/environment/evidence resolver

Goal:

All major load-development screens can ask the same service for one engine state.

### Block 2: harmonics + seating + component interaction

Connect next:

- `rifle_harmonics.py`
- jump/seating data
- internal ballistics
- pressure plausibility
- bullet and lot evidence

Goal:

The engine can say why a combination looks promising or fragile.

### Block 3: rifle learning

Add:

- charge-window learning
- seating-window learning
- lot effect learning
- accepted/confirmed candidate memory

Goal:

The engine improves per rifle over time.

### Block 4: candidate generator and next-test planner

Add:

- candidate ranking
- next-step ranking
- “do not change this yet” guardrails
- recommendation confidence

Goal:

The engine becomes useful before the user fires unnecessary test rounds.

### Block 5: replace fragmented local intelligence

Move existing UI logic to consume engine output instead of recomputing parallel mini-judgments.

Goal:

The app behaves as one smart system instead of many smart widgets.

## Robustness Requirements

Before calling the engine production-ready, ensure:

- no hard dependency on external AI or network
- missing fields degrade gracefully
- older `analysis_json` payloads do not break runtime
- stale `QSettings` state is ignored safely
- batch/workspace UI state never overrides real evidence state
- every engine recommendation includes confidence and blocking conditions

## Safety Rule

The engine may say:

- ammo/process signal is strong
- ammo/process signal is weak
- evidence is mixed
- non-ammo influence is plausible

It must not pretend to diagnose the shooter as a fact.

The decision model should focus on whether ammo is sufficiently supported as the cause.

## Short Conclusion

The codebase already contains most of the domain pieces needed to build the intended product.

The correct next step is not to build more disconnected modules.

The correct next step is to connect:

- rifle profile
- component profile
- harmonics
- seating/jump
- lot learning
- measured evidence
- decision rules

into one local, self-learning ammo engine that the rest of the app reads from.
