"""
Avansert treningslogg-modul for skyteanalyse
- Fritekst/notater
- Automatisk bildeanalyse og scoring
- MOA/gruppeberegning
- Rapportgenerator
"""

import json
from datetime import datetime

import cv2
import numpy as np


class TreningsLogg:
    def __init__(self, loggfil="treningslogg.json"):
        self.loggfil = loggfil
        self.logg = []
        self.load()

    def load(self):
        try:
            with open(self.loggfil, "r", encoding="utf-8") as f:
                self.logg = json.load(f)
        except FileNotFoundError:
            self.logg = []

    def save(self):
        with open(self.loggfil, "w", encoding="utf-8") as f:
            json.dump(self.logg, f, indent=2, ensure_ascii=False)

    def add_entry(self, target_type, image_path, distance, position, notes):
        hits = self.detect_hits(image_path)
        moa = self.calculate_moa(hits, distance)
        entry = {
            "date": datetime.now().isoformat(),
            "target_type": target_type,
            "image": image_path,
            "distance": distance,
            "position": position,
            "notes": notes,
            "hits": hits,
            "moa": moa,
        }
        self.logg.append(entry)
        self.save()
        return entry

    def detect_hits(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is not None and isinstance(image, np.ndarray):
            blurred = cv2.GaussianBlur(image, (5, 5), 0)
        else:
            raise ValueError("Bilde ikke funnet eller feil format for GaussianBlur.")
        _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        hits = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 500:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    hits.append((cx, cy))
        return hits

    def calculate_moa(self, hits, distance):
        if len(hits) < 2:
            return 0.0
        # Finn største avstand mellom treff
        max_dist = 0.0
        for i in range(len(hits)):
            for j in range(i + 1, len(hits)):
                dx = hits[i][0] - hits[j][0]
                dy = hits[i][1] - hits[j][1]
                dist_px = np.sqrt(dx**2 + dy**2)
                # Forutsetter 1 px = 1 mm (juster etter bilde)
                dist_mm = dist_px
                moa = (dist_mm / distance) * 3438
                if moa > max_dist:
                    max_dist = moa
        return round(max_dist, 2)

    def generate_report(self):
        report = []
        for entry in self.logg:
            report.append(
                {
                    "date": entry["date"],
                    "target_type": entry["target_type"],
                    "distance": entry["distance"],
                    "position": entry["position"],
                    "moa": entry["moa"],
                    "notes": entry["notes"],
                }
            )
        return report


if __name__ == "__main__":
    logg = TreningsLogg()
    entry = logg.add_entry(
        target_type="DFS 100m",
        image_path="sample_100m_target.jpg",
        distance=100,
        position="liggende",
        notes="Vind fra høyre, .223 Rem, Varget, 24x kikkertsikte",
    )
    print("Loggført økt:", entry)
    print("Rapport:", logg.generate_report())
