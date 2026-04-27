"""
AI Target Helper

Eksempelmodul for AI-basert innsamling, utregning og analyse av skytemål og resultater.
Bruker OpenCV og (valgfritt) ML-modeller for bildeanalyse.
"""

import json

import cv2
import numpy as np

# Last inn target-database
with open("../data/targets_db.json", "r", encoding="utf-8") as f:
    targets_db = json.load(f)

# Eksempel: Finn treffsoner for en DFS 100m skive
skive = targets_db["DFS"]["100m"]
print("DFS 100m skive:", skive)


# Eksempel: Bildeanalyse (finn treffpunkter)
def detect_hits(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is not None and isinstance(image, np.ndarray):
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
    else:
        raise ValueError("Bilde ikke funnet eller feil format for GaussianBlur.")
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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


# Eksempel: AI-basert scoring
# (Her kan du koble til ML-modell for mer avansert analyse)
def score_hits(hits, skive):
    center_x = skive["width"] // 2
    center_y = skive["height"] // 2
    scores = []
    for cx, cy in hits:
        dx = cx - center_x
        dy = cy - center_y
        dist = np.sqrt(dx**2 + dy**2)
        score = 0
        for ring, diameter in skive["rings"].items():
            if dist <= diameter / 2:
                score = int(ring)
                break
        scores.append({"hit": (cx, cy), "score": score})
    return scores


# Eksempelbruk
hits = detect_hits("sample_100m_target.jpg")
result = score_hits(hits, skive)
print("Scoring result:", result)

# AI/ML: For avansert analyse, tren en ML-modell (f.eks. CNN) på bilder av skiver for å finne treff og klassifisere soner.
# Dette kan utvides med OCR, objektgjenkjenning, og statistisk analyse.
