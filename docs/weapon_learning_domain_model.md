# Weapon Learning Domain Model

## Purpose

This document locks the domain model needed for the program to become a real weapon-learning load-development system.

The goal is not just to store more fields.

The goal is to structure firearm, barrel, brass, batch, and test evidence so the engine can learn the correct thing at the correct level.

This document should be read together with:
- `load_module_blueprint.md`
- `load_engine_gap_analysis.md`
- `load_engine_target_spec.md`

## Core Principle

The system must not treat the whole firearm as one flat profile.

Learning must happen on the right layer.

### The correct hierarchy

1. Weapon platform
2. Barrel
3. Barrel configuration
4. Load-development session
5. Batch
6. Test session
7. Measured evidence

If these levels are mixed together, the engine will learn noisy averages instead of weapon-specific behavior.

## Canonical Entity Model

### 1. Weapon platform

This is the parent object.

It represents the host firearm or system, not one specific barrel state.

Examples:
- bolt rifle
- switch-barrel rifle
- AR-platform rifle
- pistol
- revolver

Weapon platform owns:
- name / label
- weapon type: `rifle`, `pistol`, `revolver`
- action type: `bolt`, `semi_auto`, `break_action`, `tilting_barrel`, `fixed_barrel`, `revolver`, `other`
- manufacturer / model
- serial / user reference
- chassis or stock system
- bedding style
- magazine length limit / feeding constraints
- global notes

Weapon platform does not own:
- final harmonics model
- throat/jump truth for all bullets
- barrel-specific learning
- suppressor-on / suppressor-off state

### 2. Barrel

Each weapon platform can have unlimited barrels.

This is the primary precision-learning object for long guns and still a major object for pistols.

Barrel owns:
- barrel id / label
- caliber
- barrel length
- twist rate
- twist direction
- rifling type
- groove count
- steel / material
- barrel age / round count
- chamber name
- chamber notes
- freebore
- throat angle
- throat erosion history anchor
- crown type
- thread spec

### 3. Barrel geometry for harmonics

One single barrel thickness value is not enough.

The harmonics layer should support both presets and measured geometry.

Minimum supported geometry model:
- attachment diameter / shank diameter
- midpoint diameter
- muzzle diameter
- barrel weight if known
- barrel profile preset: `straight`, `sporter`, `varmint`, `sendero`, `mtu`, `bull`, `custom`

Preferred geometry model:
- 5 to 8 diameter stations along the barrel
- station position in mm from action face
- outer diameter at each station

Barrel geometry also needs:
- fluted or not
- flute depth / flute count if known
- barrel contour notes
- whether the barrel contacts stock/forend

### 4. Barrel attachment and support

This directly affects the harmonics model and should be explicit.

Required fields:
- attachment type: `shouldered_prefit`, `barrel_nut`, `integral`, `press_fit`, `pinned`, `custom`
- support state: `free_floated`, `partial_contact`, `pressure_pad`, `unknown`
- bedding quality / repeatability note
- return-to-zero confidence when swapping barrels if applicable

### 5. Barrel configuration

The same barrel can behave differently depending on what is attached at the muzzle.

This should not be stored as a separate barrel.

It should be a selectable barrel configuration.

Barrel configuration owns:
- barrel id
- configuration label
- muzzle device type: `none`, `suppressor`, `brake`, `compensator`, `hybrid`
- muzzle device model
- muzzle device mount type
- muzzle device weight
- muzzle device length
- tuner present / tuner settings if used
- gas setting / recoil setting if relevant for semi-auto platforms

This configuration must be selectable in the load module before recommendations are generated.

## Chamber and Jump Model

The engine must learn seating depth and jump per barrel and bullet, not only per caliber.

### Required measured values

Per barrel plus bullet:
- max COAL to lands
- max CBTO to lands
- chosen jump
- chosen jam if jammed systems are intentionally used
- date of measurement
- method / tool used
- confidence / repeatability

### Historical values

These values must be historical, not overwrite-only.

Needed because:
- throat erosion changes the truth over time
- different bullets behave differently in the same chamber
- seating recommendations must know whether they rely on current or stale measurements

## Brass and Case Model

The engine should support both generic brass use and batch-specific brass learning.

### Brass archetype

Component-level case data:
- manufacturer
- caliber
- nominal case family
- small/large primer type

### Brass batch

Learning should mostly occur on brass batch level.

Required fields:
- lot / batch id
- manufacturer
- caliber
- source / purchase lot
- number of cases
- current firing count
- whether mixed or matched
- intended firearm or barrel linkage when user wants it

### Case measurements

At batch level, store repeated measurements:
- H2O capacity
- case length
- neck thickness
- case weight
- concentricity / runout
- primer pocket depth
- flash hole diameter
- trim-to length
- shoulder bump target
- anneal state and anneal history
- prep operations performed

These values should influence:
- pressure confidence
- ES/SD expectations
- load density interpretation
- recommendation robustness

## Load-Development Session

`load_development_sessions` remains the canonical runtime object.

It should bind together:
- weapon platform
- active barrel
- active barrel configuration
- mission / usage profile
- bullet
- powder
- primer
- brass batch or generic brass context
- chosen COAL / CBTO / jump
- selected lots
- subsonic mode or normal mode
- current predicted state
- current evidence state
- current learning state
- next recommended action

This object should not permanently own all measurement history.

It should reference it.

## Batch Model

A batch is the executable test artifact created from a session snapshot.

Batch owns:
- linked load session id
- weapon platform id
- barrel id
- barrel configuration id or equivalent snapshot
- component ids and lot ids
- final selected charge / seating / jump
- ammo quantity produced
- printed recipe / report payload
- analysis snapshot at creation time

The batch is what the user loads, labels, prints, and takes to the range.

## Test Session Model

One batch can have multiple test sessions.

Test session owns:
- linked batch id
- weapon platform id
- barrel id
- barrel configuration state actually used
- date / range / distance
- environmental conditions
- suppressor used yes/no
- notes on cycling / recoil / bolt lift / extraction / lockback / feeding
- tester verdict: `promising`, `neutral`, `problematic`, `finalized`

### Evidence linked to test session

Each test session can hold:
- chronograph shot strings
- target/group images
- primer images
- pressure sign notes
- measured group sizes
- zero shift observations
- velocity summary
- subsonic observations

This is the core learning loop.

## Learning Responsibilities

The engine should learn different things at different levels.

### Weapon platform learns
- general function constraints
- magazine limits
- system-specific feeding behavior
- general recoil / handling envelope

### Barrel learns
- precision tendency
- harmonic behavior
- velocity behavior in that barrel
- pressure-sign context
- jump sensitivity
- throat movement over time

### Barrel configuration learns
- suppressor or brake effect on harmonics
- suppressor-specific stability risk
- POI shift and return-to-zero behavior
- subsonic behavior with suppressor

### Brass batch learns
- capacity drift
- prep-state effects
- lifecycle and failure risk
- ES/SD contribution

### Component lot learns
- powder lot velocity offset
- temperature sensitivity
- primer-specific changes in ignition behavior

### Batch learns
- whether one exact recipe worked
- what changed versus prediction
- whether it should be iterated or frozen

## Rifle vs Pistol Rules

The system must not assume rifle behavior everywhere.

### Rifle emphasis
- harmonics are primary
- barrel geometry matters heavily
- jump and throat model matter heavily
- suppressor and brake mass can materially affect behavior

### Pistol emphasis
- harmonics are secondary support only
- function window is critical
- slide mass, recoil spring, lockup, porting, comp, and booster behavior matter more
- OAL / feeding / chambering window matters more than classic rifle node logic

### Pistol-specific platform fields

Add support for:
- slide mass
- recoil spring rate
- locked-breech vs fixed barrel
- compensator or porting
- suppressor booster type
- magazine OAL constraints
- cycling threshold observations
- power-factor oriented use case if relevant

## Recommendation Engine Rules

The recommendation engine should rank outcomes using the active context:
- weapon platform
- barrel
- barrel configuration
- bullet
- powder
- primer
- brass batch
- mission profile
- measured evidence

### Powder suitability ranking

Instead of only warning about powder, the engine should rank powders by:
- caliber fit
- bullet weight fit
- barrel length fit
- fill ratio
- burn completeness
- pressure efficiency
- temperature behavior
- subsonic suitability when enabled
- prior success history in the same barrel

### Seating guidance

Seating advice should use:
- current jump measurements
- throat erosion history
- harmonics sensitivity
- measured accuracy history
- pressure movement with seating change

### Batch iteration guidance

After test entry, the engine should answer:
- keep as candidate
- verify with repeat batch
- adjust charge
- adjust seating
- change powder family
- change brass assumptions
- stop because evidence is weak or risk is increasing

## Required UI Flow

### 1. Weapon selection

When the load module opens, the user should choose:
- weapon platform
- active barrel
- active barrel configuration

### 2. Component selection

Then choose:
- bullet
- powder
- primer
- brass batch or generic brass

### 3. Guided analysis surface

Then the user should see:
- recommended charge window
- recommended seating / jump window
- pressure and safety state
- harmonics / function state
- recoil and velocity summaries
- powder suitability ranking
- subsonic guidance when enabled

### 4. Batch creation

The user can:
- cancel
- save session only
- create batch
- print a recipe/report sheet

### 5. Post-range evidence loop

From historical batches, the user should reopen the batch and add:
- chronograph data
- target image
- primer images
- distance
- verdict and notes

That evidence must flow back to:
- batch analysis
- session recommendation update
- barrel learning profile
- brass and lot learning where relevant

## Mapping To Current Codebase

This domain model should map onto current architecture like this:

- `load_development_sessions`
  Canonical live session object

- `rifles`
  Current weapon-platform parent row

- `rifle_profile_details`
  Current holder for extended barrel lists and geometry-rich JSON

- barrel entries inside weapon profile details
  Current barrel-level state; should become stricter and more normalized over time

- `barrel_learning_profiles`
  Barrel-level learned evidence summary

- `case_learning_profiles`
  Brass/case lifecycle evidence summary

- `rifle_bullet_jump_measurements`
  Per-barrel/per-bullet jump and jam history

- `chronograph_*` tables, target analysis, primer evidence
  Test-session evidence inputs

## Implementation Priorities

### Phase 1

Lock the data contract.

Deliverables:
- explicit weapon platform fields
- explicit barrel fields
- explicit barrel configuration fields
- explicit test-session linkage rules

### Phase 2

Make load-module intake use:
- weapon
- barrel
- barrel configuration

before recommendation generation.

### Phase 3

Feed recommendation ranking from:
- powder suitability
- barrel-specific evidence
- brass-batch context
- jump history

### Phase 4

Normalize post-range evidence entry so every batch can be reopened and improved.

## Locked Design Decisions

- One weapon platform can have unlimited barrels.
- One barrel can have multiple selectable configurations.
- Learning priority is barrel first, not weapon first.
- Brass learning should happen primarily on batch level.
- Test evidence must link back into barrel learning.
- Pistol support is first-class, but with different weighting than rifle.
- Powder guidance should be ranking-based, not only warning-based.
- The load module should teach cause and effect, not only present a recipe.