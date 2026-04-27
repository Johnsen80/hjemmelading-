from __future__ import annotations

from typing import Any, Dict, Optional


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
        return {
            "error": "opencv-not-installed",
            "pixel_diameter": None,
            "mm_diameter": None,
            "n_shots": None,
        }

    try:
        img = cv2.imread(image_path)
        if img is None:
            return {
                "error": "could-not-read-image",
                "pixel_diameter": None,
                "mm_diameter": None,
                "n_shots": None,
            }
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # find contours
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # filter small contours
        blobs = [c for c in contours if cv2.contourArea(c) > 10]
        n = len(blobs)
        if not blobs:
            return {"pixel_diameter": 0.0, "mm_diameter": 0.0, "n_shots": 0}

        if n == 1:
            contour = blobs[0]
            area = float(cv2.contourArea(contour))
            pixel_diameter = float(np.sqrt((4.0 * area) / np.pi))
            moments = cv2.moments(contour)
            if moments.get("m00"):
                center_x = float(moments["m10"] / moments["m00"])
                center_y = float(moments["m01"] / moments["m00"])
            else:
                (center_x, center_y), _ = cv2.minEnclosingCircle(
                    contour.astype(np.float32)
                )
        else:
            # For multiple impacts, approximate the overall group spread.
            all_pts = np.vstack(blobs).reshape(-1, 2)
            (center_x, center_y), radius = cv2.minEnclosingCircle(
                all_pts.astype(np.float32)
            )
            pixel_diameter = float(radius * 2.0)

        mm_diameter = None
        if dpi:
            try:
                # dpi -> inches; 1 inch = 25.4 mm
                inches = pixel_diameter / dpi
                mm_diameter = inches * 25.4
            except Exception:
                mm_diameter = None
        return {
            "pixel_diameter": pixel_diameter,
            "mm_diameter": mm_diameter,
            "n_shots": n,
            "center": (center_x, center_y),
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "pixel_diameter": None,
            "mm_diameter": None,
            "n_shots": None,
        }
