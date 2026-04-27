# Load Engine Target Specification

## Goal
Build a load-development engine that is:
- robust enough to trust
- simple enough to use without friction
- deep enough for advanced users
- explicit enough to teach the user what changed and why
- conservative enough to increase shooter confidence and safety

The engine must help the user find the best practical load for the chosen purpose, not just calculate isolated values.

## Product Standard
The load engine should behave like a guided technical copilot for ammunition development.

That means it must do five things at the same time:
- understand the firearm and component context
- simulate and compare realistic changes
- explain tradeoffs clearly
- learn from verified results
- stop the user from drifting into unsafe or weak conclusions

## Current Strengths

### 1. Good technical building blocks already exist
The current system already contains:
- charge and pressure calculations
- seating-depth advisory
- harmonics-related summaries
- impact-window and hunting-specific logic
- lot-aware bullet, powder, and primer context
- batch creation and retest suggestions
- chrono and target evidence ingestion

This is a strong base. The project does not need a new engine from scratch. It needs consolidation and a stricter runtime model.

### 2. The system already thinks in evidence, not just static lookup
The current stack can use:
- historical test results
- rifle-specific jump data
- environmental measurements
- lot context
- cartridge standards

That is exactly the right direction for a high-value load engine.

### 3. The system already has the right product ambition
The codebase already points toward:
- guidance instead of only raw numbers
- purpose-based tuning
- safer defaults
- richer context than typical hobby reloading tools

## Current Weaknesses

### 1. The engine is not yet one engine
The system still behaves as several related tools:
- Smart Wizard
- Modern Load Builder
- Load Development Workflow
- Harmonics Lab
- Batch Workspace
- Ladder/Test tools

This hurts trust, because the user cannot easily tell which screen is the real source of truth.

### 2. The user is not always shown cause and effect clearly enough
The current engine can compute useful results, but it does not yet always answer the user-facing questions:
- What changed?
- Why did the recommendation move?
- Which variable caused the pressure increase?
- Is this recommendation based on simulation, published data, or my own history?
- How confident is the system?

Without that layer, even correct output can feel opaque.

### 3. Safety is present, but too distributed
Safety logic exists in several places, but the product still needs one unified safety posture.

The user should always be able to see:
- current safety state
- main risk factor
- what assumption the engine is making
- what measurement would reduce uncertainty

### 4. The engine is not yet strong enough at ranking the "best" load
Right now, parts of the system can identify useful windows, sweet spots, and strong historical evidence.

But the engine still lacks one clear best-load decision model that balances:
- pressure margin
- consistency
- group size
- intended use
- temperature robustness
- lot sensitivity
- confidence in the data

## What "Best Load" Should Mean
The engine must not chase the single highest velocity or prettiest simulation output.

It should optimize for the selected mission.

### For precision / match
Primary priorities:
- repeatable group size
- low ES and SD
- stable seating behavior
- robust node confirmation

### For hunting
Primary priorities:
- safe pressure margin
- cold-bore confidence
- impact velocity / bullet window at realistic range
- good enough precision with environmental robustness

### For training / general use
Primary priorities:
- safe, repeatable function
- simple reproducibility
- low component sensitivity
- acceptable precision and cost efficiency

### For subsonic / suppressed
Primary priorities:
- stable subsonic velocity window
- suppressor-aware safety and function
- consistency across temperature
- projectile stability and margin to transonic behavior

## Required Engine Behaviors

### 1. Single source of truth
Every load-development run needs one canonical session.

The session must own:
- firearm and barrel setup
- suppressor / brake state
- mission profile
- bullet, powder, primer, brass, and lots
- chosen COAL / CBTO / jump values
- predicted solution
- current safety status
- linked batches
- linked tests and evidence
- current best recommendation
- confidence level

### 2. Every change must produce a delta explanation
When the user changes charge, seating, bullet, powder, primer, lot, temperature, or barrel-related values, the engine must report:
- what changed numerically
- what that likely affects
- whether the change is safety-relevant
- whether the model confidence went up or down

The user must be allowed to explore these changes deliberately.

This means the engine should support interactive what-if adjustment of relevant variables so the user can understand cause and effect before committing to a test direction.

Minimum explanation format:
- Before
- After
- Effect
- Confidence
- Suggested next action

Example:
- Before: 42.3 gr, predicted 56,200 PSI, jump 0.38 mm
- After: 42.6 gr, predicted 58,400 PSI, jump unchanged
- Effect: +2,200 PSI, +18 fps, slightly smaller pressure margin
- Confidence: medium, because chrono history exists but lot evidence is limited
- Suggested next action: verify with 3-5 chrono shots before increasing further

### 3. Confidence must be first-class
Every major recommendation should carry a confidence label such as:
- low confidence
- medium confidence
- high confidence

Confidence should depend on:
- whether reference data exists
- whether rifle-specific measurements exist
- whether lot-specific evidence exists
- whether verified chrono/test results exist
- how close the current state is to previously confirmed results

### 4. Safety must be persistent and visible
The engine should always maintain a live safety assessment with at least:
- overall safety level
- main risk source
- distance to cartridge limit
- distance to lands / jump risk
- case fill and compression state
- any lot warnings
- any primer warnings

The user should not need to hunt for safety info in different modules.

### 5. Recommendation quality must improve with real evidence
The engine should learn from:
- chrono sessions
- accuracy results
- temperature tests
- lot changes
- primer changes
- seating experiments
- verified hunting/impact observations where applicable

The rule should be:
- simulation proposes
- testing verifies
- evidence updates the model

## User Experience Standard

This UX standard must be read together with [load_engine_visual_simulation_spec.md](load_engine_visual_simulation_spec.md).

The visual language, graphs, and simulation surfaces are not optional polish. They are part of the product's trust model and should be treated as first-class requirements during implementation.

### One main loading flow
The user should feel one seamless flow:
1. choose firearm and mission
2. choose components and active lots
3. get a recommended working window
4. adjust and compare changes live
5. see the effects immediately
6. create test batches
7. record evidence
8. receive updated guidance
9. lock or refine the load

### Two layers of complexity
The engine should be simple without being shallow.

#### Default layer
Show:
- recommended charge window
- recommended seating window
- safety status
- expected performance
- top three changes in plain language

#### Advanced layer
Show:
- detailed pressure model inputs
- harmonics sensitivity
- chamber-to-standard comparison
- lot confidence
- ranked evidence sources
- model assumptions and uncertainty

### The UI must answer "why" automatically
Each recommendation panel should explain:
- why the engine prefers this window
- what evidence it is using
- what could invalidate the recommendation
- what test would improve certainty fastest

### The UI must support free adjustment with immediate feedback
The user should be able to adjust important parameters and immediately see what changes.

This includes at minimum:
- charge weight
- seating depth
- COAL / CBTO / jump
- bullet choice
- powder choice
- primer choice
- lot selection
- barrel selection
- environmental assumptions where relevant

The purpose is not only to produce a recommendation, but to teach the user which variables drive pressure, velocity, consistency, harmonics, and field performance.

The UI should make it easy to answer questions like:
- what happens if I add 0.2 grains?
- what happens if I move seating depth 0.10 mm?
- what changes if I keep the bullet but switch powder?
- what changes if I keep the load but change primer or lot?
- what changes if I use a different pipe?

### The UI must also feel unique and technically credible
The product should not look like a generic form-based utility.

It should feel like a purpose-built ballistics and load-development console with:
- strong visual identity
- high-density but readable data views
- distinctive graph language
- simulation-first comparison surfaces
- clear separation between measured, inferred, and simulated values

## Data and Learning Standard

### Bullet data
Bullet data is already one of the stronger areas.
It should continue to drive:
- geometry
- BC choice and segmented drag behavior
- impact-window logic
- seating evidence comparison
- lot-aware performance context

### Powder data
Powder data is currently the strongest simulation-oriented component domain.
It should remain the backbone of:
- burn-rate interpretation
- internal-ballistics assumptions
- load density and compression analysis
- lot drift awareness

### Primer data
Primer data should be upgraded from mostly component/advisory status to a stronger engine role.

Needed improvements:
- clearer primer-pressure interaction guidance
- better primer-lot learning summaries
- function/reliability implications by use case

### Cartridge standard data
Cartridge standards should be the authoritative limit layer for:
- pressure ceilings
- OAL references
- chamber comparison
- neck/freebore checks

All load-engine safety views should prefer this shared standard source over hardcoded fallback data whenever available.

## Safety Model Requirements

### Conservative defaults
The engine should default to caution when:
- the cartridge standard is uncertain
- the selected lot differs from validated history
- the bullet is near or into the lands
- powder model data is incomplete
- throat erosion has shifted geometry enough to matter
- the suppressor state changes from the validated setup

### No silent certainty
The engine must never present uncertain conclusions as if they are measured truth.

Every major advisory should indicate whether it comes from:
- published reference data
- inferred simulation
- measured user evidence
- lot history
- chamber comparison

### What reduces uncertainty should always be shown
The product should explicitly tell the user what to do next to improve trust:
- chrono 5 shots
- verify cold-bore point of impact
- remeasure jam CBTO
- verify with active lot
- repeat one control batch

## Robustness Requirements

### Engine code
To be robust, the load engine needs:
- one canonical session service
- explicit relationships between session, batch, and evidence
- fewer broad queries against global test tables
- deterministic linking of new evidence back to the active session

### Validation
The load engine needs focused tests for:
- session lifecycle
- recommendation updates after new evidence
- safety-state transitions
- lot changes
- suppressor / brake state changes
- chamber-standard mismatch warnings
- seating and pressure delta explanations

### Traceability
Every important recommendation should be reproducible later.
The session should store:
- input snapshot
- model output snapshot
- evidence used
- recommendation revision
- explanation text

## Recommended Rebuild Priorities

### Priority 1. Canonical session model
Without this, the engine stays fragmented.

### Priority 2. Unified recommendation surface
Modern Load Builder should become the main operational surface for one active session.

### Priority 3. Explainability layer
Add explicit before/after/delta/confidence messaging for every important change.

### Priority 4. Unified safety layer
Expose one persistent safety panel that follows the session everywhere.

### Priority 5. Evidence-driven best-load ranking
Introduce one scoring layer that ranks candidate loads for the selected purpose based on both prediction and measured results.

## Definition of Done
The load engine is "good enough" only when:
- users no longer need to jump between separate loading tools to complete one load journey
- every recommendation has visible confidence and reason
- every important change explains what happened
- safety state is always visible and conservative
- verified test results feed back into the same session and update guidance
- the engine can defend why one candidate is the best current load for the user’s purpose

## Final Position
The project already has the ingredients for a first-class load engine.

What it still lacks is unification, traceability, and a stronger explainability layer.

If those three areas are solved well, the load engine can become the part of the product that creates the most trust, the most unique value, and the strongest long-term learning advantage.

## Locked Execution Plan

The following execution order is locked until explicitly changed:

1. Lock barrel, chamber, and fired-case model
2. Define measurement hierarchy and data trust
3. Build component and lot model
4. Build firearm, barrel, and component matching
5. Connect chronograph and group evidence
6. Build one unified load-development flow
7. Build per-barrel learning engine
8. Rank optimal load combinations
9. Connect ballistics to measured evidence
10. Build data intake and analysis pipeline
11. Clean, anonymize, and structure shareable insight
12. Secure the whole flow with end-to-end validation

Execution rules:
- Do not reorder these steps casually.
- Do not create competing data models beside the canonical model.
- Favor existing rifle, barrel, case, jump, chrono, target, and session structures where possible.
- Treat measured user data as stronger than catalog or estimated values once sufficiency checks pass.
- Keep confidence, evidence source, and safety state visible in every important recommendation.

## Phase 1: Canonical Barrel, Chamber, and Fired-Case Model

Phase 1 is the foundation for the rest of the smart engine. The goal is not to invent a new subsystem, but to consolidate existing rifle, barrel, chamber, jump, and case-capacity structures into one operational truth model.

### Core principle

The engine should learn from the actual barrel and chamber, not just from cartridge-level assumptions.

That means fired brass should be treated as sensor data for the selected barrel and chamber.

At the same time, the engine must keep bullet, powder, primer, brass, and lot data as first-class domains.

The smart engine is therefore built on interaction between:
- firearm
- active barrel
- chamber geometry
- fired-case evidence
- bullet data
- powder data
- primer data
- brass and brass-lot data
- measured results from chrono and target evidence

### Canonical entities

The following entities should be treated as canonical in Phase 1:

#### 1. Firearm
Base host record.

Current foundation already exists in:
- `rifles`
- `rifle_profile_details`

Responsibilities:
- hold platform-level identity and configuration
- hold generic geometry only when no active barrel override exists
- provide the parent relationship for active barrel selection

#### 2. Barrel profile
Primary barrel-specific truth.

Current foundation already exists in:
- `rifle_profile_details.profile_json[barrels]`
- `barrel_learning_profiles`
- `barrel_profiles` where relevant

Responsibilities:
- selected barrel identity
- barrel geometry and twist
- muzzle device state
- chamber context relevant to that barrel
- barrel-specific case measurement summary
- barrel-specific learning state

Required barrel fields for smart use:
- barrel id
- barrel name
- caliber
- barrel length
- twist
- barrel profile / contour
- round count
- throat erosion estimate
- chamber spec source: SAAMI, CIP, match, custom
- max magazine COAL if relevant
- selected muzzle device state

#### 3. Chamber measurements
This is where chamber-specific user data must live.

Current foundation already partially exists in:
- rifle fields for freebore, throat angle, leade length
- `rifle_bullet_jump_measurements`
- barrel details JSON

Required chamber fields:
- max chamber COAL measured by user
- jam COAL
- jam CBTO
- bullet used for jam measurement
- measurement method
- measurement tool
- measurement variation
- rounds fired at measurement
- freebore / leade / throat fields when known
- case-head or base-to-datum expansion reference where the user tracks it

Rule:
These values must be stored as measured chamber data, not silently merged into generic cartridge assumptions.

#### 4. Fired-case measurement set
The fired-case set is the pipe-aware feedback layer.

Current foundation already partially exists in:
- `cases`
- `case_measurements`
- `case_learning_profiles`
- `case_firing_log`
- barrel `case_measurements` JSON already used by ballistics services

Required fired-case fields:
- linked firearm id
- linked barrel id
- linked case id or brass batch id
- manufacturer and lot
- times fired
- H2O capacity per sample
- minimum sample count
- neck diameter before/after
- base diameter before/after
- shoulder datum / bump when available
- trim length
- neck thickness
- case weight when available
- notes on pressure signs or outliers

Rule:
Fired-case data used by the smart engine must be explicitly tied to the selected barrel, not just to a generic brass record.

### Minimum sufficiency rules

The smart engine should not treat all data as equally trustworthy.

#### H2O / case capacity
- Fewer than 3 samples: informational only
- 3 to 9 samples: usable with low confidence
- 10 or more samples: normal measured baseline
- More than 10: preferred, increases confidence if spread is controlled

#### Chamber/jam measurements
- Single measurement: provisional
- Repeated measurement with recorded variation: trusted
- Old measurement with high round-count drift since capture: degrade confidence

#### Fired-case geometry
- One-off measurements: advisory only
- Repeated series on same barrel and same brass lot: eligible for smart recommendations

### Data priority model

When multiple values exist for the same concept, the engine should prefer them in this order:

1. Verified measured user data from the active barrel and relevant lot
2. Verified historical results from the same barrel
3. User-entered barrel profile values without repeated evidence
4. Component catalog or cartridge standard reference data
5. Estimated fallback values

This priority order must be explicit in code and visible in explanations.

### Phase 1 output requirements

At the end of Phase 1, the system should be able to answer:
- Which barrel is active?
- What chamber-specific measurements exist for that barrel?
- What fired-case measurements exist for that barrel and brass lot?
- Which bullet, powder, primer, and brass lots are active or referenced in the session context?
- Is the H2O baseline strong enough to trust?
- Is the jam / CBTO baseline current enough to trust?
- Which values are measured, inferred, or estimated?

### Implementation constraints

Phase 1 should avoid a destructive schema rewrite.

Implementation should:
- reuse existing `rifles`, `rifle_profile_details`, `case_measurements`, `case_learning_profiles`, `case_firing_log`, and `rifle_bullet_jump_measurements`
- move toward one canonical access layer rather than more scattered direct reads
- keep backward compatibility with existing rifle and load workflows
- add missing barrel-linked fields only where the current schema cannot carry the required meaning

### Definition of done for Phase 1

Phase 1 is done only when:
- the application has one clear canonical model for firearm, active barrel, chamber data, and fired-case evidence
- fired-case H2O and geometry data are barrel-linked and not treated as loose notes
- chamber length / jam / CBTO data are tied to measured context and aging over round count
- every downstream engine can tell whether a value is measured, inferred, or estimated
- confidence gating is possible before ranking loads or adapting ballistics