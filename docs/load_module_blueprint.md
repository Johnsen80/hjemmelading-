# Load Module Blueprint

## Purpose

This document locks a concrete implementation direction for the load module based on what already exists in code.

The goal is not to redesign the module from scratch.

The goal is to consolidate the current load-development stack into one technically credible, visually distinctive, and learning-oriented product surface.

## Scope

This blueprint is only about the load module.

It covers:
- session model
- workflow entry points
- evidence flow
- learning signals
- simulation and what-if behavior
- visual product identity for load development

It should be read together with:
- `load_engine_target_spec.md`
- `load_engine_visual_simulation_spec.md`
- `project_todo.md`

## What already exists

The current codebase already contains a strong technical foundation.

### Existing entry points

- `src/modules/modern_load_builder.py`
  Primary interactive builder with safety summaries, component context, lot handling, and ballistic analysis.

- `src/modules/smart_loading_wizard.py`
  Guided recommendation flow that already creates canonical load-development sessions.

- `src/modules/load_development_workflow.py`
  Protocol-oriented workflow layer with purpose profiles and test-plan logic.

- `src/ui/main_window.py`
  Current shell entry logic that decides whether the user lands in Batch Workspace or Modern Load Builder.

### Existing canonical data structures

- `load_development_sessions`
  The canonical runtime/session table for current and future load work.

- `barrel_learning_profiles`
  Existing per-rifle/per-barrel learning structure with confidence, chrono samples, target samples, and drift-related fields.

- `case_learning_profiles`
  Existing learning structure for brass/case history and reuse.

- `rifle_bullet_jump_measurements`
  Existing measured jump/jam data used by the pressure and seating logic.

- `chronograph_imports`, `chronograph_sessions`, `chronograph_readings`
  Existing velocity evidence pipeline.

### Existing calculation layers

- `src/modules/ballistics_engine.py`
  Already contains pressure, seating-depth effect, jump-aware warnings, and harmonics-related calculations.

- `src/modules/load_data_service.py`
  Already exposes neutral summary/evidence services for load cards and profile trust.

## Main problem in the current load module

The problem is not missing data.

The problem is that the module still behaves like several adjacent tools instead of one coherent load engine.

### Current fragmentation

The module currently spreads responsibility across:
- Smart Wizard
- Modern Load Builder
- Load Development Workflow
- Batch Workspace
- legacy loading session concepts

This creates three product problems:

1. The user cannot always tell which screen is the real source of truth.
2. Similar logic is expressed in multiple places with slightly different framing.
3. The system has enough data to feel smart, but not yet one surface that makes that intelligence obvious.

## Locked source-of-truth decisions

These decisions should guide all further implementation in the load module.

### 1. `load_development_sessions` is the canonical load runtime

All active load-development work should flow through one canonical session state.

That session should own:
- selected rifle
- active barrel
- mission or usage profile
- active bullet, powder, primer, brass, and lots
- chamber and jump context
- recommendation state
- evidence summary
- learning state
- confidence state
- next action

No new parallel runtime model should be introduced if the same role can be served by `load_development_sessions` plus supporting evidence services.

### 2. `modern_load_builder.py` should become the primary expert work surface

This module already has the right shape for the future load cockpit.

It should become the main high-density working view for:
- interactive adjustment
- immediate delta feedback
- evidence review
- session comparison
- safety and confidence inspection

### 3. `smart_loading_wizard.py` should become guided intake into the same session model

The smart wizard should remain a guided front door, not a separate load engine.

Its responsibility should be:
- gather intent and context
- create or update the canonical load-development session
- hand the user off to the same downstream recommendation and evidence model

### 4. `load_development_workflow.py` should own protocol guidance, not competing runtime state

This module should remain responsible for:
- test methodology
- protocol selection
- batch planning
- exit criteria
- next-step guidance

It should not become a separate truth source for live load state.

### 5. `ballistics_engine.py` should remain a calculation layer, not a product center

The ballistics engine should provide calculations and risk interpretation.

The product-facing explanation, ranking, and evidence presentation should be handled in dedicated load-module services above it.

## What makes this load module unique

The unique value is not a single pressure number or a generic load recommendation.

The unique value is that the program should learn the interaction between:
- firearm
- active barrel
- chamber geometry
- fired brass behavior
- bullet
- powder
- primer
- brass lot
- measured chrono results
- measured group results
- temperature and environment

That means the module should behave like a digital load-development cockpit for one real weapon system.

## Product identity for this module

The load module should feel like one dedicated work surface.

### Core experience

The user should be able to:
- select a known weapon and active barrel
- load an existing session or create a new one
- see the active component and lot context immediately
- adjust variables freely
- understand what changed and why
- compare measured evidence to simulated output
- see trust and safety status at all times
- decide the next test based on evidence instead of guesswork

### Required visual surfaces

The load module should converge on five recognizable surfaces:

1. Session header strip
   Shows active weapon, barrel, mission, components, lots, confidence, and safety state.

2. Charge and node surface
   Shows charge versus predicted and measured velocity, pressure margin, ES/SD, and group tendencies.

3. Seating and jump surface
   Shows jump or CBTO versus pressure and precision behavior.

4. Evidence timeline
   Shows how chrono, groups, lot changes, and barrel learning evolved over time.

5. Delta inspector
   Shows before, after, effect, confidence, and suggested next action for every user adjustment.

## Immediate implementation target

The best next technical move is not another wizard page.

The best next move is one consolidation layer for the load module.

### Build a canonical load-session runtime service

Create one service layer that assembles the live load state from existing tables and services.

That runtime should unify:
- `load_development_sessions`
- rifle and active barrel context
- barrel learning profile
- case learning profile when relevant
- jump data
- current component and lot selections
- chrono evidence
- target or group evidence
- recommendation state
- confidence and safety summary

This should become the single object that the main load UI consumes.

### Why this is the best next step

Because it unlocks all of the following without duplication:
- one source of truth in UI
- one consistent delta explanation layer
- one confidence model
- one safety strip
- one future graph adapter model
- one learning update path

## Suggested implementation order inside the load module

### Phase A. Consolidate runtime

Build a load-session runtime assembler over existing tables and services.

Deliverables:
- canonical runtime payload for the active load session
- normalized active component and lot context
- normalized barrel and chamber context
- normalized evidence summary

### Phase B. Define influence and evidence model

Build a strict distinction between:
- measured values
- inferred values
- simulated values
- fallback assumptions

Every major output in the load module should carry that classification.

### Phase C. Add interactive delta engine

When the user changes charge, seating depth, jump, bullet, powder, primer, lot, or barrel, the module should generate:
- before state
- after state
- affected outputs
- strongest driver
- confidence shift
- recommended next action

### Phase D. Build weapon/barrel/component match layer

Add a scoring and explanation layer for:
- bullet-to-barrel fit
- powder-to-purpose fit
- lot robustness
- primer suitability
- case readiness

This should not be a black box. It should explain why the score moved.

### Phase E. Build the load cockpit UI

Use the consolidated runtime and delta engine to turn `modern_load_builder.py` into the real load cockpit.

### Phase F. Close the learning loop

New chrono or target evidence should update:
- barrel learning
- lot confidence
- recommendation strength
- next test direction

## Guardrails

The following should be treated as hard rules for this module.

### Do not create new parallel truth models

If a concept already exists in:
- `load_development_sessions`
- `barrel_learning_profiles`
- `case_learning_profiles`
- chrono tables
- target or accuracy tables

then new code should extend or normalize that path instead of inventing a second storage model.

### Do not let UI modules own domain truth

UI files should render and manipulate the canonical runtime.

They should not become the long-term owner of scattered recommendation logic.

### Do not collapse measured and simulated data into one visual style

If the user cannot distinguish measured evidence from model output quickly, trust will drop.

## Best immediate product opportunities

These are the highest-value features for the load module after runtime consolidation.

1. A persistent evidence and confidence strip at the top of the load cockpit.
2. A live what-if delta panel for charge, seating, jump, and lot changes.
3. A charge-node graph overlaying measured and simulated results.
4. A barrel-learning timeline that shows what the system has learned about the active pipe.
5. A component-lot influence view that explains how lots change velocity, consistency, and trust.

## Summary

The load module already has the raw material needed to become a strong, differentiated product.

The next leap should come from consolidation, not feature sprawl.

If the module is rebuilt around one canonical runtime, one delta model, and one visual load cockpit, it can become:
- unique
- visually credible
- genuinely learning-oriented
- much easier to trust