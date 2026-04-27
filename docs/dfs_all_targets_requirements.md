# DFS Target Requirements: 100m, 200m, 300m

## DFS 100m Target (Skive)
- Standard size: 42cm x 42cm (verify with Skytterboka)
- Concentric scoring rings (bullseye, 10-ring, 9-ring, etc.)
- Example ring diameters (approximate, update with official values):
  - 10-ring: ~3cm
  - 9-ring: ~6cm
  - 8-ring: ~9cm
  - ...
  - 1-ring: ~42cm (edge)

## DFS 200m Target (Skive)
- Standard size: 1m x 1m
- See previous file for ring examples

## DFS 300m Target (Skive)
- Standard size: 1.5m x 1.5m (verify with Skytterboka)
- Concentric scoring rings, similar structure
- Example ring diameters (approximate):
  - 10-ring: ~15cm
  - 9-ring: ~30cm
  - ...
  - 1-ring: ~150cm (edge)

## Electronic Target Screens
- Scoring zones identical to paper targets
- Display may show only hit location and score
- For image analysis: account for screen artifacts, resolution, cropping

## Image Analysis/Test Plan
- Support 100m, 200m, and 300m targets
- Detect scoring rings, center, and hit location
- Handle both paper and screen-photo input
- Validate against official ring diameters
- Golden test set: include all three distances, both paper and screen-photo

---

*Update all ring diameters and target sizes with official DFS Skytterboka values for production use.*
