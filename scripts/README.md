# DFS Target Ring Detection Example

This script (dfs_target_ring_detection.py) demonstrates how to detect scoring rings on DFS 100m, 200m, or 300m targets using OpenCV. 

- Update RING_DIAMETERS_MM and TARGET_SIZE_MM for each target type (see docs/dfs_all_targets_requirements.md).
- Place a sample image (e.g., dfs_200m_sample.jpg) in the same folder.
- The script outputs an image with detected rings overlaid.

## Requirements
- Python 3.x
- OpenCV (`pip install opencv-python`)
- numpy

## Usage
1. Place your target image in this folder.
2. Run the script:
   ```
   python dfs_target_ring_detection.py
   ```
3. Check the output image for detected rings.

See docs/dfs_all_targets_requirements.md for official target specs.
