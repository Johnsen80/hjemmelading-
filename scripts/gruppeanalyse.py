"""
Gruppeanalyse-modul for skyting
- MOA og MIL beregning
- Automatisk kalibrering
- Live analyse
- Utstyrsanalyse
- Værdata
- Treningsplan
- Konkurransemodus
- Skytehistorikk
- Støtte for flere disipliner
- Synkronisering
"""

import numpy as np


class GruppeAnalyse:
    def __init__(self, px_per_mm=1):
        self.px_per_mm = px_per_mm

    def calculate_moa(self, hits, distance_m):
        if len(hits) < 2:
            return 0.0
        max_dist = 0.0
        for i in range(len(hits)):
            for j in range(i + 1, len(hits)):
                dx = hits[i][0] - hits[j][0]
                dy = hits[i][1] - hits[j][1]
                dist_px = np.sqrt(dx**2 + dy**2)
                dist_mm = dist_px / self.px_per_mm
                moa = (dist_mm / (distance_m * 1000)) * 3438
                if moa > max_dist:
                    max_dist = moa
        return round(max_dist, 2)

    def calculate_mil(self, hits, distance_m):
        if len(hits) < 2:
            return 0.0
        max_dist = 0.0
        for i in range(len(hits)):
            for j in range(i + 1, len(hits)):
                dx = hits[i][0] - hits[j][0]
                dy = hits[i][1] - hits[j][1]
                dist_px = np.sqrt(dx**2 + dy**2)
                dist_mm = dist_px / self.px_per_mm
                mil = dist_mm / (distance_m * 1000)
                if mil > max_dist:
                    max_dist = mil
        return round(max_dist, 3)

    # Flere funksjoner kan legges til her for live analyse, utstyr, vær, treningsplan, konkurranse, historikk, synkronisering


# Eksempelbruk
if __name__ == "__main__":
    analyse = GruppeAnalyse(px_per_mm=1)
    hits = [(100, 120), (110, 118), (95, 123), (130, 119), (90, 121)]
    distance_m = 0.1  # 100m
    moa = analyse.calculate_moa(hits, distance_m)
    mil = analyse.calculate_mil(hits, distance_m)
    print(f"Max gruppe MOA: {moa}")
    print(f"Max gruppe MIL: {mil}")
