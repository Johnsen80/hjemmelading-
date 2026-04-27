"""
DFS Target Shot Detection and Scoring Example

This script detects shot holes and assigns scores based on ring detection for DFS 100m, 200m, or 300m targets.
Update RING_DIAMETERS_MM and TARGET_SIZE_MM with official values for production.
"""

import cv2
import numpy as np

# Example: DFS 200m target (update for 100m/300m as needed)
RING_DIAMETERS_MM = [
    1000,
    900,
    800,
    700,
    600,
    500,
    400,
    300,
    200,
    100,
]  # 1-ring to 10-ring (mm)
TARGET_SIZE_MM = 1000  # 1m x 1m

# Load image (replace with your file)
image = cv2.imread("dfs_200m_sample.jpg", cv2.IMREAD_GRAYSCALE)
if image is None:
    raise FileNotFoundError("Image file not found.")

# Preprocess: blur and threshold
blurred = cv2.GaussianBlur(image, (5, 5), 0)
_, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

# Detect shot holes (contours)
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
shot_centers = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if 50 < area < 500:  # Adjust area range for typical shot holes
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            shot_centers.append((cx, cy))

# Assume target center is image center
center_x = image.shape[1] // 2
center_y = image.shape[0] // 2

# Scoring
scores = []
for cx, cy in shot_centers:
    dx = cx - center_x
    dy = cy - center_y
    dist_px = np.sqrt(dx**2 + dy**2)
    # Convert pixel distance to mm
    px_per_mm = image.shape[0] / TARGET_SIZE_MM
    dist_mm = dist_px / px_per_mm
    # Find score
    score = 1
    for i, ring_d in enumerate(RING_DIAMETERS_MM[::-1]):
        if dist_mm <= ring_d / 2:
            score = 10 - i
            break
    scores.append({"center": (cx, cy), "score": score, "distance_mm": dist_mm})

# Draw results
output = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
for shot in scores:
    cv2.circle(output, shot["center"], 5, (0, 0, 255), -1)
    cv2.putText(
        output,
        str(shot["score"]),
        (shot["center"][0] + 10, shot["center"][1]),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 0, 0),
        2,
    )

cv2.imwrite("dfs_200m_scored.jpg", output)
print("Shot detection and scoring complete. Output saved as dfs_200m_scored.jpg")
for shot in scores:
    print(
        f"Shot at {shot['center']}: Score {shot['score']} (distance {shot['distance_mm']:.1f} mm)"
    )
