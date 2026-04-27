# Load Engine Gap Analysis

## Purpose
This document captures the technical gaps between the current load-development implementation and the target product direction: one unified, learning load engine that guides the user from rifle selection to batch creation, test capture, analysis, and the next recommended step.

## Current State Summary
The codebase already contains strong building blocks:
- guided recommendation flow in `smart_loading_wizard.py`
- deeper interactive load work in `modern_load_builder.py`
- planning and advisory logic in `load_development_workflow.py`
- persistence and follow-up in `batch_workspace.py`
- pressure, seating-depth, and harmonics calculations in `ballistics_engine.py`

The main weakness is not lack of features. The weakness is that the load process is still spread across several entry points, tables, and UI flows.

## Core Findings

### 1. The load engine is split across multiple entry points
Current entry points route users into different tools instead of one canonical load flow.

Observed in:
- `src/ui/main_window.py`
- `src/modules/smart_loading_wizard.py`
- `src/modules/modern_load_builder.py`
- `src/modules/load_development_workflow.py`
- `src/modules/batch_workspace.py`

Impact:
- users are still sent to different modules depending on mode or action
- important state is duplicated or inferred later
- the product does not yet behave like one coherent loading engine

### 2. Smart wizard is advisory, not authoritative
`SmartLoadingWizard.accept()` currently writes a lightweight record to `loading_sessions` and mostly stores recommendation notes.

Impact:
- no canonical handoff into a unified load-development session
- no direct ownership of component lots, seating plan, retest plan, or workflow state
- useful guidance is produced, but the engine does not take control of the next steps

### 3. Workflow planning and execution are separated
`load_development_workflow.py` has strong planning functions such as test-plan generation, impact-window guidance, and component verification advisory.

Impact:
- the advisory layer is good
- execution state is still spread across UI components and database tables
- recommendations are not consistently attached to one active load session that evolves over time

### 4. The persistence model is fragmented
The current process uses several overlapping storage concepts:
- `load_development_workflows`
- `loading_sessions`
- `ladder_tests`
- `test_results`
- workflow context in `QSettings`

Impact:
- there is no single source of truth for one load-development run
- batch generation, chrono imports, target analysis, and workflow suggestions must rediscover context instead of reading one canonical session object
- learning across the full process becomes weaker and harder to trust

### 5. Learning is partial and local, not system-wide
The engine can already use:
- previous chrono rows
- previous ladder results
- bullet jump measurements
- environment observations

But this is done in isolated places rather than through one persistent learning profile.

Impact:
- rifle knowledge is reused inconsistently
- batch/test outcomes do not always feed back into the same engine model
- the user experience still feels like multiple tools with partial memory

### 6. Physics and safety models are useful but still generalized
The seating-depth and harmonics calculations are valuable, but parts of the model are still broad approximations.

Examples:
- seating depth pressure uses an empirical constant
- harmonics rely on simplified barrel-profile mapping
- UI flows use more detailed barrel descriptions than the harmonics layer actually models

Impact:
- guidance is directionally useful
- confidence and traceability are not yet strong enough for the system to present itself as a tightly personalized weapon-learning engine

### 7. Test ingestion is connected, but not fully normalized into one loop
`modern_load_builder.py` can save chrono data into `test_results`, suggest retests, and poll for new results.

Impact:
- strong infrastructure already exists
- the feedback loop still depends on shared tables and heuristics instead of one formal session lifecycle

### 8. Operational robustness is not where it needs to be yet
Focused test execution around the load engine is currently sensitive to environment/path setup.

Impact:
- the code can be valid while still being too brittle to validate quickly
- this increases the chance of regressions while consolidating the load engine

## Main Architectural Gap
The current implementation has several smart loading tools.

The target product needs one canonical load engine with:
- one session model
- one lifecycle
- one context source
- one learning loop

That is the single biggest gap.

## Target Architecture

### Canonical entity: Load Development Session
Introduce one primary session record that represents the full load journey.

Suggested responsibilities:
- selected rifle and barrel setup
- suppressor or brake state
- intended use profile
- chosen components and lots
- planned powder window and seating window
- measured jump and jam references
- live simulation snapshot
- recommended next action
- linked batches
- linked chrono imports
- linked target-analysis outputs
- linked verification sessions
- confidence/advisory state
- learning state summary

This session should be the object that all major tools read from and write back to.

### Canonical lifecycle
The engine should move through a clear state machine:
1. rifle and mission selection
2. component and lot selection
3. recommended load window generation
4. interactive tuning and simulation
5. batch creation
6. test capture
7. evidence analysis
8. recommendation update
9. verify or finalize

### Unified context propagation
Remove reliance on ad hoc handoff patterns where possible.

Replace with:
- session id passed explicitly between views
- database-backed session state
- lightweight UI state only for transient presentation details

`QSettings` can still be used for UI convenience, but not as the main workflow backbone.

## Concrete Gaps By Module

### `smart_loading_wizard.py`
Strengths:
- good intent capture
- useful recommendation summary
- decent starting advisory for purpose and historical data

Gaps:
- creates a lightweight `loading_sessions` record instead of a canonical load-engine session
- does not become the first stage of the main engine
- does not directly launch or hydrate the next step with authoritative state

Required change:
- make Smart Wizard the intake stage for the unified load engine, or merge its logic into the canonical intake flow

### `modern_load_builder.py`
Strengths:
- strongest interactive engine surface
- batch creation exists
- retest advisor exists
- chrono to test-result ingestion exists

Gaps:
- still works partly as its own world
- reads broad `test_results` pools instead of always working from one explicit session context
- appears to bridge into workflow records instead of owning the full lifecycle directly

Required change:
- reframe this as the main execution surface for a canonical load-development session

### `load_development_workflow.py`
Strengths:
- strongest planning layer
- impact-window logic is solid directionally
- usage-profile logic is valuable

Gaps:
- primarily advisory/planning oriented
- not the single runtime engine for the user journey

Required change:
- keep this module as policy/planning logic, but let it feed a canonical engine session instead of standing alone as a separate workflow path

### `batch_workspace.py`
Strengths:
- already aware of workflow context
- useful place for post-build evidence, attachments, chrono, and follow-up

Gaps:
- consumes workflow context indirectly
- should not need to infer the active load state from scattered settings and tables

Required change:
- batch workspace should open against an explicit canonical load session or linked batch object

### `ballistics_engine.py`
Strengths:
- useful safety and harmonics helpers
- seating-depth pressure effect and jump logic are already present

Gaps:
- still partly generalized
- some barrel-profile detail is lost before reaching the model
- confidence level is not surfaced strongly enough

Required change:
- preserve richer barrel and rifle descriptors
- attach assumptions and confidence to the returned advisory payloads
- let measured rifle history tune future estimates

## Data Model Problems To Solve
Current overlapping records create ambiguity.

### Existing tables involved
- `load_development_workflows`
- `loading_sessions`
- `ladder_tests`
- `test_results`
- `rifle_bullet_jump_measurements`

### Recommended direction
Keep the current tables for compatibility short term, but introduce one authoritative session linkage strategy.

At minimum, every relevant record should be traceable to:
- `load_session_id`
- `rifle_id`
- `batch_id` where applicable
- `workflow_id` only if legacy compatibility is still needed

## Recommended Build Order

### Phase 1. Canonical session contract
Define one session schema and service layer for the load engine.

Deliverables:
- canonical session model
- create/update/read service
- explicit linkage strategy for batch, test, and recommendations

### Phase 2. Intake unification
Route Smart Wizard output into the canonical session.

Deliverables:
- intake flow writes one real session
- next screen opens with hydrated data
- recommendation payload is persisted structurally, not as notes only

### Phase 3. Builder unification
Make Modern Load Builder operate directly on the canonical session.

Deliverables:
- builder reads and writes canonical session state
- batch creation links back to the session
- retest recommendations are stored on the session

### Phase 4. Evidence loop unification
Link chrono, target analysis, ladder tests, and batch workspace back into the same session.

Deliverables:
- all evidence artifacts attach to session id
- next-step recommendation is regenerated from session evidence
- history becomes weapon-aware and lot-aware

### Phase 5. Learning layer
Add persistent rifle-plus-load learning summaries.

Deliverables:
- per-rifle learned tendencies
- per-bullet and per-lot tendencies
- confidence scoring and evidence summaries

## Risks During Refactor
- breaking legacy flows that still open older tools directly
- losing compatibility with existing `test_results` and `loading_sessions`
- silently degrading safety guidance if assumptions are not preserved
- creating more fragmentation if new session logic is added without routing all tools through it

## Short-Term Rule Set
Until the unified engine is complete, all new work in the loading domain should follow these rules:
- no new standalone load-related entry points
- all new recommendations must be attachable to one explicit session context
- all new batch/test integrations must carry session linkage where possible
- safety assumptions must be surfaced, not hidden in free-text notes

## Conclusion
The load engine is not broken. It is already promising.

But it is not yet one engine.

Today, the product has multiple smart tools for load work.
The next milestone is to turn them into one canonical, learning load-development system.