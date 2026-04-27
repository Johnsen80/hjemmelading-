# Bullet Intelligence Roadmap

## Why this track comes first

Bullet intelligence is the highest-value next step because it sits directly in the user's selection flow and builds on capabilities that already exist in the codebase:

- bullet geometry and profile inference in `src/ballistics/services.py`
- twist and gyroscopic stability estimation in `src/ballistics/services.py`
- impact window and terminal suitability summary in `src/ballistics/services.py`
- advisory presentation patterns in `src/modules/modern_load_builder.py`
- future orchestration point in `src/modules/digital_twin.py`

This makes it possible to deliver a meaningful feature without first rebuilding the whole engine.

## Product principles

The bullet intelligence feature set must follow five rules:

1. Simple first
The default view should answer three questions immediately: does this bullet fit the rifle, does it fit the intended use, and what should the user test next.

2. User-adjustable
Every recommendation can be overridden by the user. The system recommends, but does not lock the workflow.

3. Easy return to recommended
Any user-adjusted value must have a clear path back to the recommended baseline. The user should never wonder what the original recommendation was.

4. Visual and legible
The state of a bullet choice should be visible through scores, bands, chips, cards, and small plots instead of only long text paragraphs.

5. Evidence-aware
The system must separate measured data, manufacturer data, inferred values, and heuristic estimates. Confidence is part of the output, not a hidden implementation detail.

## North-star experience

When the user selects a bullet, the app should immediately show:

- Bullet Fit Score: how well the bullet matches the rifle and twist.
- Stability Card: SG, twist margin, suppressor risk, and subsonic margin where relevant.
- Geometry Card: bullet family, base, tip, construction, length, diameter, seating sensitivity hints.
- Flight Card: BC basis, drag model, segmented BC if available, wind drift and spin drift preview.
- Game Suitability Card: small game, medium game, large game suitability with confidence and impact-window logic.
- Recommendation Card: the recommended baseline setup and the next best test if confidence is not high enough.

## Interaction model

Each adjustable parameter in this feature track should support three states:

- Recommended: the system default based on current evidence.
- Custom: user override currently active.
- Learned: recommendation adjusted by accepted evidence or calibration.

Each such control should expose:

- the current value
- the recommended value
- the recommendation source
- a `Use recommended` action
- a `Reset all bullet guidance` action at section level

Recommended visual treatment:

- small state chip next to the control: `Recommended`, `Custom`, or `Learned`
- subdued helper line under the field: `Recommended from twist + SG model` or `Learned from accepted field data`
- one-click restore button next to fields that have been overridden
- section-level summary banner when the current setup differs materially from recommended

## Build order

### Phase 1: Bullet Fit Analyzer

Goal: answer whether the bullet fits the rifle and why.

Scope:

- combine existing geometry inference, Greenhill guidance, and SG estimation
- show fit score and severity level
- show twist margin and missing-data warnings
- show suppressor and subsonic stability notes where relevant
- show seating sensitivity hints for long or VLD-like bullets

Primary outputs:

- `fit_score`
- `fit_level`
- `fit_title`
- `fit_message`
- `checks`
- `recommended_baseline`

Code anchors:

- `src/ballistics/services.py`
- `src/modules/modern_load_builder.py`

### Phase 2: Game Suitability Advisor

Goal: provide an honest, useful hunting suitability assessment without pretending to simulate wound channels.

Scope:

- classify suitability for `small_game`, `medium_game`, and `large_game`
- use impact velocity, impact energy, construction, tip type, bullet family, and known minimum working window
- surface confidence explicitly
- warn when the result is heuristic rather than evidence-backed

Important limitation:

This phase must be framed as suitability guidance, not biological simulation.

Primary outputs:

- `game_class`
- `suitability_level`
- `confidence_label`
- `confidence_message`
- `impact_window_summary`
- `failure_reasons`

### Phase 3: Bullet Terminal Data Model

Goal: prepare for stronger predictions later.

Add a structured `terminal_data` block, likely inside `profile_json` first and later optionally in a dedicated table.

Minimum desired fields:

- `minimum_expansion_fps`
- `preferred_impact_min_fps`
- `preferred_impact_max_fps`
- `minimum_energy_ftlbs`
- `construction_type`
- `tip_type`
- `core_bonding`
- `rest_weight_percent_estimate`
- `expansion_ratio_estimate`
- `penetration_class`
- `bone_tolerance_class`
- `game_class_min`
- `game_class_max`
- `evidence_level`
- `evidence_source`

These fields must support four provenance levels:

- measured
- manufacturer
- curated reference
- heuristic inferred

### Phase 4: Digital Twin Integration

Goal: move bullet intelligence from static advisory to living context.

`src/modules/digital_twin.py` should eventually combine:

- rifle context
- bullet profile and terminal data
- powder and primer lot learning
- actual chrono and target observations
- accepted engine calibration

The bullet part of the twin should track:

- predicted fit confidence
- predicted impact-window confidence
- measured deviations from expected velocity or stability
- suggested next verification step

### Phase 5: Evidence-Driven Recommendation Engine

Goal: make the system feel genuinely smart and hard to replace.

This layer should answer:

- what is the current recommended bullet baseline
- what has the user overridden
- what is the safest next action
- what is the highest-value next test
- how much confidence should the user place in the current recommendation

Recommendation priority order:

1. safety and stability
2. fit to intended use
3. evidence quality
4. performance optimization

## Visual design rules

This track should follow the design brief in `docs/design_system_brief.md`.

Required UI patterns:

- summary cards instead of long prose blocks
- small range bars or confidence bands for fit and impact window
- compact chips for state and confidence
- at least one visual comparison between recommended and current setup
- consistent teal primary, amber warning, red critical, neutral surfaces

Suggested visual modules:

- Fit meter: 0-100 with risk banding
- Twist gauge: actual twist vs recommended twist range
- Impact window bar: current impact velocity placed against minimum and preferred band
- Drift preview: wind drift and spin drift side by side

## Simplicity rules for implementation

To keep the feature easy to work with, do not spread the main bullet decision logic across many UI methods.

Preferred structure:

- one service function to build bullet fit context
- one service function to build game suitability context
- one small presenter/formatter per screen
- UI widgets consume structured payloads instead of recomputing logic

This keeps the feature testable and easy to evolve.

## Data honesty rules

The app must never imply certainty it does not have.

Allowed phrases:

- `looks suitable`
- `likely usable`
- `estimated working window`
- `heuristic guidance`
- `confidence: medium`

Avoid phrasing that implies lab-grade certainty unless the evidence is real and explicit.

## Recommended next implementation step

Build `Phase 1: Bullet Fit Analyzer` first.

Why:

- it uses data already present
- it helps every user immediately
- it creates the visual and interaction shell for later phases
- it establishes the recommended-vs-custom state model that later smart logic can reuse

## Success criteria

This track is successful when:

- a user can select a bullet and immediately understand if it fits the rifle
- a user can override recommendations without losing the baseline
- a user can see why the recommendation exists
- a user can return to the recommended state with one click
- the app can later reuse the same model for learning and digital twin logic