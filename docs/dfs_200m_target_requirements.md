# DFS 200m Target and Electronic Scoring Requirements

## DFS 200m Target (Skive)
- Standard size: 1m x 1m
- Concentric scoring rings (bullseye, 10-ring, 9-ring, etc.)
- Example ring diameters (verify with DFS Skytterboka):
  - 10-ring: ~10cm
  - 9-ring: ~20cm
  - 8-ring: ~30cm
  - 7-ring: ~40cm
  - 6-ring: ~50cm
  - 5-ring: ~60cm
  - 4-ring: ~70cm
  - 3-ring: ~80cm
  - 2-ring: ~90cm
  - 1-ring: ~100cm (edge)
- Paper targets: Black center, white outer rings

## Electronic Target Screens
- Systems: Kongsberg, W5, etc.
- Scoring zones identical to paper targets
- Display may show only hit location and score
- For image analysis:
  - Account for screen artifacts, resolution, cropping
  - Preprocessing may be needed (contrast, color, geometry)

## Image Analysis/Test Plan
- Support both paper and screen-photo input
- Detect scoring rings, center, and hit location
- Handle partial/cropped images (screen photos)
- Validate against official ring diameters
- Golden test set: Include both paper and screen-photo examples

---

*Update ring diameters with official DFS Skytterboka values for production use.*
