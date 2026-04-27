"""
Feilanalyse-modul for skyting
- AI/statistikk for å oppdage tekniske feil
- Skiller mellom skytter, våpen, ammunisjon
- Gir forslag til forbedring
"""

import numpy as np


class Feilanalyse:
    def __init__(self):
        self.feilmønstre = {
            "avtrekksfeil": {
                "pattern": "horisontal",
                "hint": "Typisk avtrekksfeil gir treff til venstre/høyre.",
            },
            "pustefeil": {
                "pattern": "vertikal",
                "hint": "Pustefeil gir vertikal spredning.",
            },
            "grepfeil": {
                "pattern": "spredning",
                "hint": "Dårlig grep gir stor spredning.",
            },
            "ammo": {
                "pattern": "random",
                "hint": "Ujevn spredning kan skyldes ammunisjon.",
            },
            "rifle": {
                "pattern": "systematisk",
                "hint": "Systematiske avvik kan skyldes rifla.",
            },
        }

    def analyse(self, hits, logg_entry):
        # hits: liste av (x, y)
        # logg_entry: dict med info om ammo, rifle, skytter, etc.
        result = {"feil": [], "hint": ""}
        if len(hits) < 2:
            return result
        xs = [h[0] for h in hits]
        ys = [h[1] for h in hits]
        spread_x = np.std(xs)
        spread_y = np.std(ys)
        # Enkel heuristikk
        if spread_x > spread_y * 1.5:
            result["feil"].append("avtrekksfeil")
            result["hint"] = self.feilmønstre["avtrekksfeil"]["hint"]
        elif spread_y > spread_x * 1.5:
            result["feil"].append("pustefeil")
            result["hint"] = self.feilmønstre["pustefeil"]["hint"]
        elif spread_x > 20 and spread_y > 20:
            result["feil"].append("grepfeil")
            result["hint"] = self.feilmønstre["grepfeil"]["hint"]
        # Ammo/våpen
        if logg_entry.get("ammo_quality", "") == "dårlig":
            result["feil"].append("ammo")
            result["hint"] += " " + self.feilmønstre["ammo"]["hint"]
        if logg_entry.get("rifle_condition", "") == "slitt":
            result["feil"].append("rifle")
            result["hint"] += " " + self.feilmønstre["rifle"]["hint"]
        # Skytter
        if logg_entry.get("position", "") in ["stående", "knestående"]:
            result["hint"] += " Stillingen kan gi mer spredning."
        return result


if __name__ == "__main__":
    feilanalyse = Feilanalyse()
    hits = [(100, 120), (110, 118), (95, 123), (130, 119), (90, 121)]
    logg_entry = {
        "ammo_quality": "dårlig",
        "rifle_condition": "slitt",
        "position": "stående",
    }
    result = feilanalyse.analyse(hits, logg_entry)
    print("Feilanalyse:", result)
