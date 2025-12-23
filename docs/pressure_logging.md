Pressure logging
================

This project records predicted peak pressures and manual pressure observations to the `pressure_history` table.

How it works

- Predictions made by the ballistics engine (or conservative estimates) are logged when running optimizers or saving test results.
- Pressure observations (signs of overpressure) can be attached to shooting sessions or ladder tests and are stored in `pressure_signs`.
- The UI (Modern Load Builder) includes a Pressure Log viewer with filters and CSV export.

Quick usage

- To export recent logged pressures, open the "Pressure Log" panel and use the date filters and "Export CSV" button.
- To associate a pressure measurement with a QC batch or test result, attach the chronograph import or test result when available.

Notes

- Pressure logging is conservative and should not replace instrumented pressure testing with certified equipment.
- Use the calibration and environmental correction features to improve predicted values.
