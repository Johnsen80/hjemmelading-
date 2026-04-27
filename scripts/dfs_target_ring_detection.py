"""
DFS Target Ring Detection Example

This script demonstrates how to detect concentric rings on DFS 100m, 200m, or 300m targets using OpenCV.
Update RING_DIAMETERS_MM with official values for production.
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

# Detect circles (Hough Transform)
circles = cv2.HoughCircles(
    thresh,
    cv2.HOUGH_GRADIENT,
    dp=1.2,
    minDist=20,
    param1=50,
    param2=30,
    minRadius=10,
    maxRadius=image.shape[0] // 2,
)

# Draw detected circles
output = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
if circles is not None:
    circles = np.around(circles).astype(int)
    for i in circles[0]:
        cv2.circle(output, (i[0], i[1]), i[2], (0, 255, 0), 2)

cv2.imwrite("dfs_200m_detected_rings.jpg", output)
print("Detection complete. Output saved as dfs_200m_detected_rings.jpg")
