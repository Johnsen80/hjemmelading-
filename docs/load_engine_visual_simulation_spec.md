# Load Engine Visual and Simulation Specification

## Goal
Define a locked visual and simulation standard for the load-development product.

This specification is cross-cutting. It applies across the plan and should influence builder views, workflow views, chronograph analysis, target analysis, component comparison, and ballistics surfaces.

The objective is not merely to make the program look nice. The objective is to make the product feel unique, technically serious, and immediately trustworthy.

## Product position
The program should feel like a precision lab console for shooters and reloaders.

It must not feel like:
- a generic business dashboard
- a plain desktop CRUD tool
- a spreadsheet with tabs
- a hobby calculator with a few plots attached

It should feel like:
- a ballistic workbench
- a load-development cockpit
- a simulation and evidence console

## Locked visual principles

### 1. Visual identity must be distinctive
The product should have an unmistakable visual language.

Requirements:
- strong typography hierarchy
- technical, premium color system
- consistent use of data-focused mono text for measurements
- recognizable simulation and evidence panels
- a visual tone that feels calm, precise, and advanced

### 2. Graphs are first-class product surfaces
Charts should not be treated as supporting decoration.

Charts are where trust is built, because that is where the user sees:
- measured data
- modeled behavior
- uncertainty
- drift over time
- comparisons between candidate loads

### 3. Simulations must feel interactive and comparative
Simulation views should help the user understand what changes when a variable moves.

The user should be able to see cause and effect, not just a single static answer.

This is a hard product requirement.

The user must be able to tune variables freely and inspect how each adjustment affects the output.

### 4. Measured and simulated data must always be visually distinct
The UI must never blur together:
- measured values
- inferred values
- simulated values
- fallback estimates

This distinction should be clear in labels, legends, styles, and explanation text.

## Core screen character

### Main working surface
The main working area should behave like a technical canvas, not a long settings form.

Preferred composition:
- left: workflow or comparison navigation
- center: primary graph/simulation surface
- right: inspector for assumptions, warnings, and deltas
- top: mission, active weapon/barrel, active load, confidence, and safety state

### Information density
The product should support dense information, but never chaotic information.

Requirements:
- layered detail
- readable defaults
- advanced drilldown without visual collapse
- low-friction switching between summary and depth

## Graph system requirements

### Graph families that must exist

#### 1. Charge sweep graphs
Purpose:
- compare predicted and measured velocity
- compare pressure margin
- identify node regions
- expose flat spots and unstable zones

Should support:
- charge on x-axis
- velocity, ES/SD, pressure, or group size on y-axis
- overlays for multiple powders or lots
- uncertainty bands
- highlighted recommended window

#### 2. Seating depth and jump graphs
Purpose:
- show how CBTO, COAL, or jump affects pressure, group size, and consistency

Should support:
- jump or CBTO on x-axis
- group size, pressure estimate, or velocity stability on y-axis
- recommended bands and warning bands

#### 3. Chronograph distributions
Purpose:
- show stability, not just average velocity

Should support:
- shot sequence view
- distribution / spread view
- temperature overlay when available
- lot comparison

#### 4. Group and target result comparison
Purpose:
- connect actual on-target performance to the load decision

Should support:
- series-to-series comparison
- image plus extracted metrics
- POI shift visualization
- cold-bore versus warm-bore distinction

#### 5. Barrel learning and drift views
Purpose:
- show how the barrel changes over time

Should support:
- round count on x-axis
- throat erosion, velocity drift, pressure drift, or precision drift on y-axis
- maintenance events and barrel changes marked on timeline

#### 6. Ballistic trajectory and field graphs
Purpose:
- connect load choice to real-world use

Should support:
- drop, drift, retained velocity, and impact energy
- measured versus predicted muzzle baseline
- environmental overlays
- distance bands relevant to the selected mission

## Visual rules for graphs

### 1. Use consistent semantics
Color and style should mean the same thing everywhere.

Examples:
- measured data: solid, high-contrast lines or points
- simulated data: lighter line with model styling
- estimated fallback: muted or dashed
- warning region: amber/red background bands
- recommended region: teal/green highlight band

### 2. Show uncertainty explicitly
For important outputs, the graph should show:
- confidence band
- tolerance band
- sample count
- spread or variation indicator

### 3. Make deltas easy to read
When the user compares two candidate loads, the graph should clearly show:
- baseline
- candidate
- numerical delta
- recommendation outcome

### 4. Preserve readability under density
If many series are shown, the graph system should still preserve:
- strong legend logic
- focus/highlight behavior
- muted background series
- filtering by component, lot, barrel, or session

## Simulation surface requirements

### 1. Simulation panels must invite comparison
Simulation should not be shown as one answer card only.

Every important simulation area should support side-by-side or overlay comparison between:
- load A and load B
- lot A and lot B
- barrel state A and barrel state B
- measured baseline and modeled variant

They should also support fast iterative what-if work where a user changes one variable at a time and sees the effect immediately.

Minimum adjustment controls should exist for:
- charge
- seating depth
- COAL / CBTO / jump
- bullet
- powder
- primer
- lot
- barrel
- environment when relevant

### 2. Simulations must explain assumptions
Every simulation surface should visibly show:
- what barrel context is used
- what chamber context is used
- what case capacity source is used
- whether values are measured or estimated
- which lot assumptions are active

### 3. Simulations must integrate safety and confidence
The user should not need to leave the simulation view to understand:
- safety margin
- confidence level
- weakest assumption
- recommended next validation step

### 4. Variable influence must be visible
The simulation UI should make it obvious which variables are driving the result.

When a user adjusts a parameter, the surface should clearly indicate:
- what moved
- which outputs changed
- which outputs changed the most
- whether the result is still inside the recommended or safe window
- whether the new view is based on measured evidence, simulation, or fallback assumptions

## Unique product markers

To feel unique, the product should develop recognizable visual signatures.

Recommended product markers:
- a persistent evidence and confidence strip near the top of working views
- a distinctive delta card pattern for before/after comparisons
- a recognizable node window visualization for charge and seating analysis
- a consistent measured-versus-modeled overlay language
- a barrel-learning timeline unique to this product

These should become part of the product identity, not one-off UI ideas.

## Minimum visual quality bar

The product is below standard if:
- graphs feel generic or bolted on
- measured and simulated values are hard to distinguish
- views are dominated by forms rather than analysis surfaces
- the same type of data is drawn differently in each module
- simulations are static and hard to compare

The product is on standard if:
- the user can immediately see the active barrel, active components, confidence, and safety state
- the main graph tells a clear story at a glance
- deeper detail is available without cluttering the default view
- visual identity feels specific to this product and domain
- charts and simulations make decisions easier, not just prettier

## Relationship to the locked roadmap

This visual specification must influence at least these roadmap steps:
- Step 5: connect chronograph and group evidence
- Step 6: build one unified load-development flow
- Step 8: rank optimal load combinations
- Step 9: connect ballistics to measured evidence

It is also a non-negotiable standard for future builder, workflow, chrono, target, and ballistics UI work.