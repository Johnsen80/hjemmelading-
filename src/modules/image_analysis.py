from __future__ import annotations

from typing import Dict, Optional, Any


def analyze_group_image(image_path: str, dpi: Optional[float] = None) -> Dict[str, Any]:
    """Attempt to analyze a target image and return group metrics.

    Returns a dict with keys: `pixel_diameter`, `mm_diameter` (if dpi provided),
    and `n_shots` (number of detected blobs). This is a best-effort helper that
    uses OpenCV if available; otherwise it returns an informative error dict.
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        return {"error": "opencv-not-installed", "pixel_diameter": None, "mm_diameter": None, "n_shots": None}

    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "could-not-read-image", "pixel_diameter": None, "mm_diameter": None, "n_shots": None}
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # find contours
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # filter small contours
        blobs = [c for c in contours if cv2.contourArea(c) > 10]
        n = len(blobs)
        # compute convex hull of all blob points to get spread
        all_pts = np.vstack(blobs) if blobs else None
        if all_pts is None:
            return {"pixel_diameter": 0.0, "mm_diameter": 0.0, "n_shots": 0}
        all_pts = all_pts.reshape(-1, 2)
        (x, y), radius = cv2.minEnclosingCircle(all_pts.astype(np.float32))
        pixel_diameter = float(radius * 2.0)
        center_x = float(x)
        center_y = float(y)
        mm_diameter = None
        if dpi:
            try:
                # dpi -> inches; 1 inch = 25.4 mm
                inches = pixel_diameter / dpi
                mm_diameter = inches * 25.4
            except Exception:
                mm_diameter = None
        return {"pixel_diameter": pixel_diameter, "mm_diameter": mm_diameter, "n_shots": n, "center": (center_x, center_y)}
    except Exception as exc:
        return {"error": str(exc), "pixel_diameter": None, "mm_diameter": None, "n_shots": None}
