# Weapon Learning Schema Plan

## Purpose

This document translates the locked domain model in `weapon_learning_domain_model.md` into a concrete schema and migration plan for the current codebase.

The goal is to improve the existing architecture without breaking the current load module flow.

This is an implementation document.

It answers:
- what can be reused as-is
- what should be extended
- what must be normalized next
- what order the migration should happen in

## Current Assets We Should Reuse

The current codebase already contains most of the foundation needed for a serious weapon-learning system.

### Keep as primary parent entity

`rifles`

Current strength:
- already stores weapon type, action type, caliber, barrel dimensions, rifling, chamber data, maintenance, magazine length, and some harmonics-related fields

Interpretation going forward:
- treat this table as the weapon-platform parent record
- do not treat it as the whole truth for multi-barrel learning

### Keep as extended profile store

`rifle_profile_details`

Current strength:
- already stores richer JSON state for barrels and profile detail

Interpretation going forward:
- this remains the compatibility bridge for the current UI
- it should hold the richer barrel and geometry contract until more of it is normalized into relational tables

### Keep as canonical active runtime

`load_development_sessions`

Current strength:
- already stores rifle, barrel, usage profile, component selection, recommendation, evidence summary, and learning state

Interpretation going forward:
- this remains the main runtime truth for active load development
- it needs explicit support for barrel configuration selection and richer component/test linkage

### Keep as barrel-learning summary

`barrel_learning_profiles`

Current strength:
- already tracks barrel-level confidence, chrono samples, target samples, drift, throat erosion, and barrel-specific profile JSON

Interpretation going forward:
- this stays the barrel-level aggregate learning surface
- it should continue to represent learned state, not raw observations

### Keep as brass-learning summary

`case_learning_profiles`

Current strength:
- already tracks case capacity, spread, firing events, prep events, anneal events, and lifecycle risk

Interpretation going forward:
- keep it as a component-level learning summary
- supplement with stronger brass-batch linkage where the user is actually testing one batch of brass in one barrel

### Keep as current batch and follow-up flow

`batch_projects`
`batch_project_sessions`

Current strength:
- already model the user-facing batch and post-range session workflow better than older `ladder_tests` and `test_results`

Interpretation going forward:
- treat these as the primary batch/test loop for the modern load engine
- extend them instead of introducing a competing second workflow system

## Main Gaps In The Current Schema

### 1. Barrel configuration is implicit, not explicit

Today:
- barrel-level JSON contains muzzle-device fields
- runtime can reason about suppressor/brake state
- but there is no explicit selectable barrel-configuration entity

Impact:
- suppressor-on and suppressor-off evidence are easy to mix
- return-to-zero, harmonics, and subsonic learning cannot be cleanly partitioned by configuration

### 2. Jump measurements are not truly barrel-specific

Today:
- `rifle_bullet_jump_measurements` keys on `rifle_id` and `bullet_id`
- it does not explicitly store `barrel_id`

Impact:
- multi-barrel rifles can leak jump truth across barrels
- this is a high-priority scientific-model gap

### 3. Barrel geometry is only partially normalized

Today:
- `rifles` stores breech/mid/muzzle diameters and some contour data
- `rifle_profile_details.profile_json` can store richer barrel JSON and measurement points

Impact:
- the data exists, but it is split between a flat rifle table and free-form JSON
- the harmonics engine still sees less structure than the UI can capture

### 4. Batch test sessions do not fully encode active barrel configuration

Today:
- `batch_project_sessions` tracks batch, distance, weather-like data, notes, photos, and analysis JSON
- but it does not have explicit normalized fields for barrel configuration, suppressor state, verdict, and function observations

Impact:
- some evidence remains hidden in notes or JSON
- recommendation logic cannot rank evidence as cleanly as it should

### 5. Weapon-platform versus barrel truth is still mixed in runtime

Today:
- `rifles` contains both platform-level and barrel-like fields
- `rifle_profile_details` adds barrel-specific detail

Impact:
- acceptable for compatibility
- but future logic must treat `rifles` as the platform parent and barrel JSON/records as the real precision object

## Recommended Target Schema Strategy

The right move is not a destructive redesign.

The right move is a compatibility-preserving, staged normalization.

## Phase 1: Lock The Data Contract Without Breaking UI

### Keep these as canonical for now

- `rifles`
- `rifle_profile_details`
- `load_development_sessions`
- `batch_projects`
- `batch_project_sessions`
- `barrel_learning_profiles`
- `case_learning_profiles`

### Add these fields to `load_development_sessions`

Required additions:
- `barrel_configuration_id TEXT`
- `barrel_configuration_name TEXT`
- `barrel_configuration_snapshot_json TEXT`
- `component_lots_json TEXT`
- `subsonic_mode INTEGER DEFAULT 0`
- `session_verdict TEXT`

Reason:
- the active runtime must know exactly which barrel state the recommendation was built for

### Add these fields to `batch_projects`

Required additions:
- `barrel_id TEXT`
- `barrel_name TEXT`
- `barrel_configuration_id TEXT`
- `barrel_configuration_name TEXT`
- `barrel_configuration_snapshot_json TEXT`
- `usage_profile_key TEXT`
- `subsonic_mode INTEGER DEFAULT 0`

Reason:
- the batch must snapshot the exact weapon/barrel/configuration context that the user actually loaded for

### Add these fields to `batch_project_sessions`

Required additions:
- `rifle_id INTEGER`
- `barrel_id TEXT`
- `barrel_name TEXT`
- `barrel_configuration_id TEXT`
- `barrel_configuration_name TEXT`
- `suppressor_used INTEGER`
- `muzzle_device_type TEXT`
- `function_status TEXT`
- `tester_verdict TEXT`
- `primer_observation_json TEXT`
- `chronograph_summary_json TEXT`

Reason:
- current post-range sessions need enough normalized context to become usable learning evidence

## Phase 2: Fix Scientific Linkage Errors

### Extend `rifle_bullet_jump_measurements`

Required additions:
- `barrel_id TEXT`
- `barrel_name TEXT`
- optional later: `barrel_configuration_id TEXT`

New lookup standard:
- primary key logic should become: `rifle_id + barrel_id + bullet_id + measurement_date`

Reason:
- this is one of the most important correctness fixes for switch-barrel rifles

### Extend `pressure_signs`

Current table already includes:
- `rifle_id`
- `barrel_id`
- `barrel_name`
- `batch_id`
- `load_session_id`

Required additions:
- `barrel_configuration_id TEXT`
- `muzzle_device_type TEXT`
- `primer_image_set_json TEXT`

Reason:
- pressure-sign evidence must be attributable to the actual barrel state used during firing

## Phase 3: Introduce Explicit Barrel Configuration Entity

Add a new table:

`barrel_configurations`

Suggested fields:
- `id INTEGER PRIMARY KEY`
- `rifle_id INTEGER NOT NULL`
- `barrel_id TEXT NOT NULL`
- `config_key TEXT NOT NULL`
- `config_name TEXT NOT NULL`
- `muzzle_device_type TEXT`
- `muzzle_device_model TEXT`
- `muzzle_device_weight_g REAL`
- `muzzle_device_length_mm REAL`
- `mount_type TEXT`
- `tuner_present INTEGER DEFAULT 0`
- `tuner_settings_json TEXT`
- `gas_setting TEXT`
- `recoil_setting TEXT`
- `is_default INTEGER DEFAULT 0`
- `notes TEXT`
- `created_date TEXT DEFAULT CURRENT_TIMESTAMP`
- `updated_date TEXT DEFAULT CURRENT_TIMESTAMP`

Unique key recommendation:
- `UNIQUE(rifle_id, barrel_id, config_key)`

Reason:
- this gives the load module one explicit configuration selector
- suppressor/brake/no-device states stop being hidden in loose JSON

### Compatibility rule

During transition:
- existing barrel JSON inside `rifle_profile_details` remains the editable source
- a sync layer can materialize simple default configurations from current barrel muzzle fields

## Phase 4: Normalize Barrel Geometry Only Where It Pays Off

Do not normalize every barrel detail immediately.

Start with a targeted geometry table:

`barrel_geometry_points`

Suggested fields:
- `id INTEGER PRIMARY KEY`
- `rifle_id INTEGER NOT NULL`
- `barrel_id TEXT NOT NULL`
- `station_index INTEGER NOT NULL`
- `position_mm REAL NOT NULL`
- `diameter_mm REAL NOT NULL`
- `source TEXT`
- `created_date TEXT DEFAULT CURRENT_TIMESTAMP`

Unique key recommendation:
- `UNIQUE(rifle_id, barrel_id, station_index)`

Reason:
- the harmonics engine needs structured geometry more than the general UI does
- this is the minimum normalization that unlocks better physics later

### Keep these in JSON for now

Still acceptable inside `rifle_profile_details.profile_json` during transition:
- contour notes
- support observations
- bedding notes
- custom attachment comments
- harmonics notes

## Phase 5: Promote Batch Sessions To Canonical Test Evidence

Use `batch_project_sessions` as the main post-range test object.

Do not add a competing `test_sessions` table.

Instead, extend current batch-session rows so they can hold:
- exact barrel context
- exact barrel configuration context
- measured chrono summary
- measured group summary
- primer/pressure observations
- functional verdict
- user decision: continue or freeze

### Evidence storage rule

Raw heavy evidence can stay linked through:
- attachments
- chronograph import references
- image paths
- analysis JSON

But ranking-critical facts should live in real columns.

## Mapping Of Current Tables To Target Model

### Weapon platform

Primary table:
- `rifles`

Potential future extensions to add when needed:
- `platform_family TEXT`
- `feeding_system TEXT`
- `stock_or_chassis TEXT`
- `bedding_type TEXT`
- `magazine_system TEXT`
- `slide_mass_g REAL`
- `recoil_spring_rating TEXT`
- `lockup_type TEXT`
- `booster_type TEXT`

### Barrel

Primary storage during transition:
- barrel objects inside `rifle_profile_details.profile_json`

Current matching support:
- `barrel_learning_profiles`
- `barrel_id` and `barrel_name` fields in runtime and evidence tables

### Barrel configuration

New normalized table:
- `barrel_configurations`

### Jump history

Primary table:
- `rifle_bullet_jump_measurements`

Critical change:
- add `barrel_id`

### Brass batch

Primary table:
- `brass_batches`

Already useful supporting tables:
- `brass_lifecycle_log`
- `annealing_log`
- `die_settings`
- `case_learning_profiles`

### Active load runtime

Primary table:
- `load_development_sessions`

### Batch and test loop

Primary tables:
- `batch_projects`
- `batch_project_sessions`

## Migration Order

### Step 1

Add compatibility columns first.

Low-risk columns:
- session-level barrel configuration fields
- batch-level barrel configuration fields
- batch-session verdict and muzzle-context fields

### Step 2

Add `barrel_id` to jump measurements and begin writing it on all new saves.

Backfill rule:
- for old rows, set `barrel_id` to the then-active barrel if recoverable
- otherwise leave null and treat as weapon-level legacy evidence only

### Step 3

Introduce `barrel_configurations` and write a sync adapter from existing barrel JSON.

### Step 4

Update load-module intake so recommendations are generated from:
- weapon
- barrel
- barrel configuration

### Step 5

Update post-range flows so evidence is written back with the same explicit context.

## High-Priority Gaps To Fix First

These are the first changes that materially improve scientific trust.

1. Add barrel configuration context to `load_development_sessions`.
2. Add barrel configuration context to `batch_projects` and `batch_project_sessions`.
3. Add `barrel_id` to `rifle_bullet_jump_measurements`.
4. Make recommendation logic read the exact barrel and configuration context instead of inferring it loosely.

## Low-Priority Gaps To Leave For Later

These are useful, but should not block the first migration pass.

- fully relational storage of every barrel note field
- full pistol-specific relational expansion
- full harmonics geometry normalization beyond station points
- retirement of all legacy `loading_sessions` and `ladder_tests` paths

## Locked Implementation Decisions

- The migration must be compatibility-first.
- `load_development_sessions` stays the canonical runtime.
- `batch_projects` and `batch_project_sessions` stay the modern execution and evidence loop.
- `rifle_profile_details` remains the short-term holder for rich barrel JSON.
- `rifle_bullet_jump_measurements` must become barrel-aware.
- Explicit barrel configuration is the next missing core entity.