"""
Integrert analyse-modul
- Kombinerer treningslogg, feilanalyse og gruppeanalyse
- Støtter MOA og MIL
- Klar for utvidelse med live analyse, utstyr, vær, synkronisering
"""

from feilanalyse import FeilAnalyse
from gruppeanalyse import GruppeAnalyse
from treningslogg import TreningsLogg


class IntegrertAnalyse:
    def __init__(self, px_per_mm=1):
        self.logg = TreningsLogg()
        self.feil = FeilAnalyse()
        self.gruppe = GruppeAnalyse(px_per_mm=px_per_mm)

    def analyse_skuddserie(self, hits, distance_m, bilder=None, utstyr=None, vaer=None):
        logg_resultat = self.logg.logg_skuddserie(hits, bilder, utstyr, vaer)
        feil_resultat = self.feil.analyse(hits)
        moa = self.gruppe.calculate_moa(hits, distance_m)
        mil = self.gruppe.calculate_mil(hits, distance_m)
        return {"logg": logg_resultat, "feil": feil_resultat, "moa": moa, "mil": mil}


# Eksempelbruk
if __name__ == "__main__":
    analyse = IntegrertAnalyse(px_per_mm=1)
    hits = [(100, 120), (110, 118), (95, 123), (130, 119), (90, 121)]
    distance_m = 0.1  # 100m
    resultater = analyse.analyse_skuddserie(hits, distance_m)
    print("Logg:", resultater["logg"])
    print("Feil:", resultater["feil"])
    print("MOA:", resultater["moa"])
    print("MIL:", resultater["mil"])
