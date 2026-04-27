# Load Module Release Readiness Checklist

Updated: 2026-04-16

## Purpose

This document defines the criteria that must be true before the load module
can be shipped as a production-ready feature surface.

It is stricter than the feature roadmap. Everything below must be verified
by a human using the actual application, not only by CI tests.

---

## 1. Canonical Truth Path

- [ ] One active load session produces one consistent context across all load-core surfaces
      (builder, workflow, batch, chrono, target).
- [ ] Re-opening a session (after app restart or tab switch) restores the same rifle,
      barrel, barrel configuration, and component context as before closing.
- [ ] `barrel_configuration_id` is present and non-null in all critical advice payloads.
- [ ] No critical load advice depends on hidden QSettings / widget state when canonical
      runtime state is available.

**CI evidence:** `test_load_module_e2e_core_workflow.py::test_context_survives_reopen_with_no_measurements`

---

## 2. Engine Input Completeness

- [ ] The engine always reports which rifle, barrel, barrel configuration, component,
      lot, and evidence context it is using.
- [ ] Missing input fields degrade gracefully — they do NOT silently shift to a wrong
      context or produce a crash.
- [ ] Partial lot context (e.g. no powder lot selected) does not produce a silent error.

**CI evidence:** `test_load_module_defensive_inputs.py` (engine partial-input tests)

---

## 3. Evidence Quality Consistency

- [ ] All critical advice surfaces show `measured / modeled / derived / recommended` labels.
- [ ] `signal_hint` in evidence_summary_json is always a canonical value from
      `SPREAD_SIGNAL_HINTS` after `refresh_load_session_measurement_summary` runs.
- [ ] `pressure_or_ammo` and `insufficient_evidence` block candidate ranking and
      set `robustness_level` to `"low"`.
- [ ] 3-shot groups are capped at `"moderate"` evidence level regardless of group size.

**CI evidence:** `test_batch_analyzer_spread_learning.py`,
`test_load_module_e2e_core_workflow.py::test_signal_hint_updates_after_chrono_save`

---

## 4. Learning Loop

- [ ] `learning_state_json.model_status` transitions correctly:
      - `"raw"` with no measured data
      - `"partially_calibrated"` with chrono only or insufficient paired data
      - `"well_calibrated"` with paired velocity + group data, medium+ data strength,
        no pressure signs
- [ ] `charge_window` is persisted when evidence is strong enough (center_gr, min_gr,
      max_gr all present; min ≤ center ≤ max).
- [ ] `seating_window` is persisted from the recommendation model when present.
- [ ] `lot_drift` contains per-component drift signals when lots are active.
- [ ] `candidates.confirmed` and `candidates.rejected` persist across re-opens.
- [ ] Re-opening restores the same charge and seating baseline that was active
      before closing (no "forgetting" between sessions).

**CI evidence:** `test_load_module_defensive_inputs.py` (model_status, charge_window, candidates tests),
`test_load_module_e2e_core_workflow.py` (step 12b, 12c)

---

## 5. Recommendation and Robustness

- [ ] The recommended next test is explainable (not "collect more data" when
      data already exists).
- [ ] Robust loads rank above lucky single-series results.
- [ ] Validation gates (`do_not_change_yet`) are active and reflect blocking signals.
- [ ] Active setup and confidence basis are visible in recommendation payloads.

**CI evidence:** `test_batch_analyzer_spread_learning.py`, `test_load_development_workflow_planning.py`

---

## 6. Consumer Alignment

- [ ] The same load context produces the same recommendation basis across builder,
      runtime, batch workspace, and digital twin.
- [ ] `batch_analyzer` uses engine signal_hint from `evidence_summary_json` as
      primary input (raw-data computation is fallback only).
- [ ] No duplicate guidance/next-step logic in `modern_load_builder.py` competes
      with the canonical engine path (**known remaining gap**).

**CI evidence:** `test_load_module_e2e_core_workflow.py` (step 6: recompute_batch_analysis_from_db)

---

## 7. End-to-End Hardening

- [ ] Engine parsing is tolerant of older JSON payloads (missing fields → graceful fallback).
- [ ] `refresh_load_session_measurement_summary` can be called on any session without
      crashing, regardless of how many measurements exist (including zero).
- [ ] Stale QSettings / widget state cannot override newer real evidence once
      refresh has run.
- [ ] Regression tests cover malformed and partial inputs for all core functions.
- [ ] E2E CI test runs the full commercial path in under 60 seconds.

**CI evidence:** `test_load_module_defensive_inputs.py`, `test_load_module_e2e_core_workflow.py`

---

## 8. Manual Verification Checklist

These items cannot be verified by CI alone. A human must confirm each before release.

### 8.1 Session lifecycle

- [ ] Create new session via wizard → verify rifle + barrel + components are in session.
- [ ] Import chrono data → verify signal_hint updates in the builder/workflow UI.
- [ ] Record a target group → verify evidence quality label updates.
- [ ] Close the app and reopen → verify session context is unchanged.
- [ ] Switch between two sessions → verify no context bleeds between them.

### 8.2 Recommendation trust

- [ ] When only 3-shot groups are available, the UI shows "moderate" evidence,
      not "strong".
- [ ] When `pressure_or_ammo` signal is active, candidate ranking is blocked
      and the UI shows the gate warning.
- [ ] When charge is outside the learned window, the next-step text says to return
      to the learned baseline — not to continue tuning.

### 8.3 Learning state visibility

- [ ] After logging 3+ sessions with paired data, `model_status` is `"well_calibrated"`.
- [ ] The learned charge window (center ± tolerance) is visible somewhere in the
      builder or workflow UI.
- [ ] Confirming a load recipe via the UI persists it to `candidates.confirmed`.
- [ ] Rejecting a recipe persists it to `candidates.rejected` with a reason.

### 8.4 Robustness under real use

- [ ] The session can be opened 10 times in a row without state drift.
- [ ] Importing the same chrono file twice does not double-count evidence.
- [ ] The module works correctly with a rifle that has never had any data logged.

---

## Known Remaining Gaps (not blocking 1.0)

| Gap | Risk | Owner |
|-----|------|-------|
| `modern_load_builder.py` duplicates guidance/next-step logic | Medium | Deferred to post-1.0 |
| Cold-bore evidence not a first-class measurement channel | Low | Deferred |
| Hunting/competition "best next test" ordering incomplete | Low | Deferred |
| No integration test verifying builder → runtime → workspace alignment | Low | Deferred |

---

## Sign-off

Before marking the load module as release-ready, confirm:

1. All CI tests in this list are green.
2. All manual verification checklist items are checked.
3. Known remaining gaps are accepted as post-1.0 work or have been resolved.

Sign-off: ___________________ Date: ___________________
