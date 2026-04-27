# Valkyrie Ballistics Design System Brief (1.0)

## Goals
- Modern, precise "lab console" feel that builds trust.
- Clear information hierarchy for dense data and charts.
- Consistent UI across Beginner, Advanced, and Research modes.
- High readability for long sessions and critical decisions.

## Visual direction
- Calm, technical, and credible.
- Warm neutral surfaces with deep ink text.
- Teal accent for primary actions, amber for warnings.

## Typography
- Primary UI: Sora (clear, modern, technical).
- Secondary: Source Serif 4 (reports, long-form headings).
- Mono: IBM Plex Mono (data, IDs, measurements).

Suggested scale:
- Body: 12-14
- Section headers: 16-18
- Page headers: 22-28
- Data labels: 11-12

## Color tokens (light-first)
- --ink-900: #0B1320
- --ink-700: #2A3443
- --ink-500: #4B5563
- --surface-0: #FFFFFF
- --surface-1: #F6F4F0
- --surface-2: #EFEAE3
- --accent-500: #0D7C8C
- --accent-600: #0A6774
- --accent-100: #D8F1F1
- --success-500: #1F8A70
- --warning-500: #B45309
- --danger-500: #B91C1C
- --info-500: #2563EB

Data visualization palette (series):
- #1B4965
- #00A6A6
- #F0B429
- #E55934
- #7CB518

## Layout and spacing
- 12-column grid for major screens.
- Left nav: 240-280 width.
- Right inspector: 320 width.
- Top bar: 56 height.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48.

## Core components
- Buttons: primary (accent), secondary (outline), ghost (minimal).
- Inputs: clear label, inline units, validation states.
- Tables: sticky headers, row density toggle, quick filters.
- Cards: summary stats, quick actions, and status chips.
- Modals/wizards: stepper for Beginner flows.
- Inspector panel: contextual parameters and warnings.

## Charts and credibility
- Always show uncertainty for key outputs (bands or intervals).
- Outliers and QC flags use consistent icon + color.
- Include assumptions and model version in chart footers.

## Motion
- Page transitions: 160-200ms, ease-out.
- Chart reveal: 240ms, staggered series.
- Avoid excessive motion; prioritize clarity.

## Accessibility
- Minimum contrast: 4.5:1 for body text.
- Focus ring: 2px accent-500, visible on all controls.
- Touch targets: minimum 32x32.

## Persona modes
- Mode switch in top bar.
- Beginner: guided steps, safe defaults, simplified options.
- Advanced: full controls, higher density.
- Research: experiment timeline, metadata, annotations.

## Copy and tone
- Precise, calm, and factual.
- Avoid hype; prioritize clarity and safety.

## Implementation notes
- Encode tokens in a single QSS or style module for consistency.
- Keep charts and tables aligned to the same spacing scale.
