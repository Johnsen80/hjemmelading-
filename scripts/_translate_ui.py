"""One-shot translation script — Norwegian → English for UI files."""

import os


def translate_file(path: str, replacements: list[tuple[str, str]]) -> int:
    content = open(path, encoding="utf-8").read()
    count = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            count += 1
    open(path, "w", encoding="utf-8").write(content)
    return count


# ---------------------------------------------------------------------------
# ammo_test_window.py
# ---------------------------------------------------------------------------
AMMO_REPS = [
    # Form labels
    ('"Merke*"', '"Brand*"'),
    ('"Modell*"', '"Model*"'),
    ('"Kaliber*"', '"Caliber*"'),
    ('"Kulvekt"', '"Bullet weight"'),
    ('"Lot-nummer*"', '"Lot number*"'),
    ('"Kjøpsdato"', '"Purchase date"'),
    ('"Pris"', '"Price"'),
    ('"Butikk"', '"Store"'),
    ('"Kjøpt antall"', '"Qty purchased"'),
    ('"Gjenstående"', '"Remaining"'),
    ('"Notater"', '"Notes"'),
    ('"Dato"', '"Date"'),
    ('"Avstand"', '"Distance"'),
    ('"Temperatur"', '"Temperature"'),
    ('"Vind"', '"Wind"'),
    ('"Lufttrykk"', '"Barometric pressure"'),
    ('"Pipetilstand"', '"Barrel state"'),
    ('"Skudd i forrige streng"', '"Prior shots in string"'),
    ('"Gruppestørrelse"', '"Group size"'),
    ('"POI X (horisontalt)"', '"POI X (horizontal)"'),
    ('"POI Y (vertikalt)"', '"POI Y (vertical)"'),
    ('"Våpen"', '"Weapon"'),
    ('"Merke:"', '"Brand:"'),
    ('"Kaliber:"', '"Caliber:"'),
    ('"Lot:"', '"Lot:"'),
    # Buttons
    ('"Lagre lot"', '"Save Lot"'),
    ('"Nullstill"', '"Clear"'),
    ('"Slett"', '"Delete"'),
    ('"Lagre sesjon"', '"Save Session"'),
    ('"Ny sesjon"', '"New Session"'),
    ('"Fjern valgt"', '"Remove Selected"'),
    ('"Lagre skudd"', '"Save Shots"'),
    ('"+ Legg til skudd"', '"+ Add Shot"'),
    ('"Sammenlign"', '"Compare"'),
    ('"Vis matrise"', '"Show Matrix"'),
    ('"Eksporter CSV"', '"Export CSV"'),
    ('"Eksporter PDF"', '"Export PDF"'),
    # Table headers
    (
        '"Merke", "Modell", "Kaliber", "Vekt", "Lot-nr", "Antall igjen"',
        '"Brand", "Model", "Caliber", "Weight", "Lot #", "Qty remaining"',
    ),
    (
        '"Dato", "Våpen", "Avstand", "Snitt fps", "Gruppe"',
        '"Date", "Weapon", "Distance", "Avg fps", "Group"',
    ),
    (
        '"#", "Hastighet (fps)", "Kaldskudd", "Kalibrering", "Blindgjenger", "Lett antenning", "Ladestøp", "Utk.problem"',
        '"#", "Velocity (fps)", "Cold bore", "Calibration", "Dud", "Light strike", "FTF", "FTE"',
    ),
    (
        '"Lot-nr", "Kjøpt", "Snitt fps", "ES (fps)", "SD (fps)", "Snitt gruppe (mm)", "Reliabilitet %"',
        '"Lot #", "Purchased", "Avg fps", "ES (fps)", "SD (fps)", "Avg group (mm)", "Reliability %"',
    ),
    (
        '"Våpen", "Sesjoner", "Snitt fps", "ES (fps)", "Snitt gruppe (mm)", "Reliabilitet %"',
        '"Weapon", "Sessions", "Avg fps", "ES (fps)", "Avg group (mm)", "Reliability %"',
    ),
    (
        '"\\u2713", "Merke / modell", "Kaliber", "Lot-nr"',
        '"\\u2713", "Brand / model", "Caliber", "Lot #"',
    ),
    # Combo items
    ('"\\u2014 Velg v\\u00e5pen \\u2014"', '"\\u2014 Select weapon \\u2014"'),
    ('"Kald pipe", "Varm pipe", "Ukjent"', '"Cold bore", "Warm bore", "Unknown"'),
    ('"\\u2014 Alle merker \\u2014"', '"\\u2014 All brands \\u2014"'),
    ('"\\u2014 Alle kalibre \\u2014"', '"\\u2014 All calibers \\u2014"'),
    # Stat cards
    ('"Snittfart"', '"Avg velocity"'),
    ('"Reliabilitet"', '"Reliability"'),
    # Graph titles
    ('title="Hastighet per skudd"', 'title="Velocity per shot"'),
    ('"fps (fot/sek)"', '"fps"'),
    ('"Skudd #"', '"Shot #"'),
    ('"Snittfart (fps)"', '"Avg velocity (fps)"'),
    ('"ES (fps) \\u2014 lavere er bedre"', '"ES (fps) \\u2014 lower is better"'),
    (
        '"Snitt gruppe (mm) \\u2014 lavere er bedre"',
        '"Avg group (mm) \\u2014 lower is better"',
    ),
    ('"Reliabilitet (%)"', '"Reliability (%)"'),
    (
        '"Gruppe per v\\u00e5pen (mm \\u2014 lavere er bedre)"',
        '"Group per weapon (mm \\u2014 lower is better)"',
    ),
    (
        '"Installer pyqtgraph for grafvisning."',
        '"Install pyqtgraph for graph display."',
    ),
    # Dialog messages
    ('"Mangler data"', '"Missing data"'),
    (
        '"Merke, modell, kaliber og lot-nummer er p\\u00e5krevd."',
        '"Brand, model, caliber and lot number are required."',
    ),
    ('"Slett lot"', '"Delete lot"'),
    (
        '"Er du sikker? Alle sesjoner tilknyttet dette lotet slettes ogs\\u00e5."',
        '"Are you sure? All sessions for this lot will also be deleted."',
    ),
    ('"Velg lot"', '"Select lot"'),
    (
        '"Velg et ammo-lot fra Lot-fanen f\\u00f8rst."',
        '"Select an ammo lot from the Lot tab first."',
    ),
    ('"Ingen valgt"', '"None selected"'),
    ('"Velg minst ett lot."', '"Select at least one lot."'),
    ('"Lagre CSV"', '"Save CSV"'),
    ('"Eksportert"', '"Exported"'),
    (
        '"PDF-eksport kobles til QPrinter \\u2014 kommer i neste iterasjon."',
        '"PDF export via QPrinter \\u2014 coming in next iteration."',
    ),
    # Header subtitle
    (
        '"Registrer og sammenlign fabrikkammunisjon per lot, sesjon og v\\u00e5pen"',
        '"Register and compare factory ammunition by lot, session and weapon"',
    ),
    # Sessions label (appears twice)
    ('"Sesjoner for dette lotet"', '"Sessions for this lot"'),
    # Tab labels
    ('"\\U0001f4e6  Ammo-lot"', '"\\U0001f4e6  Ammo Lot"'),
    ('"\\U0001f3af  Test-sesjon"', '"\\U0001f3af  Test Session"'),
    ('"\\U0001f4ca  LOT-sammenligning"', '"\\U0001f4ca  Lot Comparison"'),
    ('"\\U0001f52b  V\\u00e5penmatrise"', '"\\U0001f52b  Weapon Matrix"'),
    ('"\\U0001f4c4  Rapporter"', '"\\U0001f4c4  Reports"'),
    # CSV header
    (
        '"Lot-nr,Merke,Modell,Kaliber,Avg fps,ES fps,Avg gruppe mm,Reliabilitet %"',
        '"Lot #,Brand,Model,Caliber,Avg fps,ES fps,Avg group mm,Reliability %"',
    ),
    # Report selection label
    (
        '"Velg lot-er \\u00e5 inkludere i rapporten:"',
        '"Select lots to include in the report:"',
    ),
    # Main title
    ('"Ammo Test"', '"Ammo Test"'),  # keep
    # Main window title label
    ('title = QLabel("Ammo Test")', 'title = QLabel("Ammo Test")'),  # keep
    # Lot inventory bold label
    ('"Lot Inventory"', '"Lot Inventory"'),  # already done
]

# ---------------------------------------------------------------------------
# main_window.py — navigation + section pages
# ---------------------------------------------------------------------------
MAIN_REPS = [
    # Nav buttons
    ('"V\\u00e5pen profil"', '"Weapon Profile"'),
    ('"Lade modul"', '"Load Development"'),
    ('"Komponenter"', '"Components"'),
    ('"Ballistisk modul"', '"Ballistics"'),
    ('"Batcher"', '"Batches"'),
    # Section descriptions
    (
        '"Oversikt over lade-komponenter: krut, kuler, hylser og tennhatter."',
        '"Overview of reloading components: powder, bullets, cases and primers."',
    ),
    (
        '"Tidligere ladede batcher \\u2014 historikk, statistikk og eksport."',
        '"Previously loaded batches \\u2014 history, statistics and export."',
    ),
    (
        '"Test og analyse av ladede patroner \\u2014 kronograf, gruppering og skytingslogg."',
        '"Test and analysis of loaded ammunition \\u2014 chronograph, grouping and shooting log."',
    ),
    # Landing page select label
    ('"Velg modul"', '"Select Module"'),
    # Landing page card subtitles
    ('"Rifle, pipe og optikk"', '"Rifle, barrel and optics"'),
    ('"Utvikling av nye ladninger"', '"Load development"'),
    ('"Krutt, kuler, hylser og tennhatter"', '"Powder, bullets, cases and primers"'),
    (
        '"Simulering, fallet og vindens p\\u00e5virkning"',
        '"Trajectory simulation and wind effects"',
    ),
    ('"Tidligere ladede batcher og historikk"', '"Loaded batches and history"'),
    (
        '"Kronograf, m\\u00e5l-analyse og skytingslogg"',
        '"Chronograph, target analysis and shooting log"',
    ),
    # Open button
    ('"\\u00c5pne"', '"Open"'),
    # Page title map
    ('"Lade modul"', '"Load Development"'),
    ('"V\\u00e5pen profil"', '"Weapon Profile"'),
]

# ---------------------------------------------------------------------------
# field_planning_window.py
# ---------------------------------------------------------------------------
FIELD_REPS = [
    (
        '"Felt-planlegging \\u2014 DOPE / Skytebane / Jakt"',
        '"Field Planning \\u2014 DOPE / Range / Hunting"',
    ),
    ('"Feil ved lasting av profil: {exc}"', '"Error loading profile: {exc}"'),
    ('"\\U0001f3af Skytebane"', '"\\U0001f3af Range"'),
    ('"\\U0001f98c Jakt"', '"\\U0001f98c Hunting"'),
    ('"\\U0001f324 Atmosf\\u00e6re"', '"\\U0001f324 Atmosphere"'),
    ('"\\U0001f4ab Kulens reise"', '"\\U0001f4ab Bullet Journey"'),
    ('"\\U0001f5fa Kart"', '"\\U0001f5fa Map"'),
    ('"Ingen profil lastet."', '"No profile loaded."'),
    ('"FELT-PLANLEGGING"', '"FIELD PLANNING"'),
    ('"V\\u00e5pen:"', '"Weapon:"'),
    ('"Sikte:"', '"Scope:"'),
    ('"\\u21bb Oppdater"', '"\\u21bb Refresh"'),
    ('"Trykk hPa:"', '"Pressure hPa:"'),
    ('"Vind m/s:"', '"Wind m/s:"'),
    ('"Vindretning \\u00b0:"', '"Wind direction \\u00b0:"'),
    ('"Bruk"', '"Apply"'),
    ('"\\u2601 Hent v\\u00e6r"', '"\\u2601 Fetch Weather"'),
    (
        '"Henter n\\u00e5v\\u00e6rende v\\u00e6r fra met.no for skytepostens posisjon"',
        '"Fetches current weather from met.no for the shooting post position"',
    ),
    (
        '"Kulens reise-visualisering\\n(krever pyqtgraph + beregnet trajektorie)"',
        '"Bullet journey visualization\\n(requires pyqtgraph + computed trajectory)"',
    ),
    ('"Henter v\\u00e6r fra met.no for"', '"Fetching weather from met.no for"'),
    ('"V\\u00e6r-henting feilet: {exc}"', '"Weather fetch failed: {exc}"'),
    ('"DOPE-feil: {exc}"', '"DOPE error: {exc}"'),
    (
        '"Skytepost: {point.lat:.6f}, {point.lon:.6f}"',
        '"Shooting post: {point.lat:.6f}, {point.lon:.6f}"',
    ),
    ('"M\\u00e5l {self._map_target_count}"', '"Target {self._map_target_count}"'),
]

# ---------------------------------------------------------------------------
# range_tab.py
# ---------------------------------------------------------------------------
RANGE_REPS = [
    (
        '"Skytebane \\u2014 m\\u00e5l og klikktabell"',
        '"Range \\u2014 targets and click table"',
    ),
    ('"+ Legg til m\\u00e5l"', '"+ Add Target"'),
    ('"\\u2013 Fjern valgt"', '"\\u2013 Remove Selected"'),
    ('"Beregn klikk"', '"Calculate Clicks"'),
    (
        '"M\\u00e5lliste (klikk for \\u00e5 redigere):"',
        '"Target list (click to edit):"',
    ),
    ('"Beregnede korrek\\u0441joner:"', '"Calculated corrections:"'),
    ('"Ingen beregning utf\\u00f8rt."', '"No calculation performed."'),
    ('"M\\u00e5l {n}"', '"Target {n}"'),
    ('"Ingen m\\u00e5l \\u00e5 beregne."', '"No targets to calculate."'),
    ('"Feil ved beregning: {exc}"', '"Calculation error: {exc}"'),
    ('"Beregnede korreksjoner:"', '"Calculated corrections:"'),
]

# ---------------------------------------------------------------------------
# hunting_tab.py
# ---------------------------------------------------------------------------
HUNTING_REPS = [
    ('"Jakt \\u2014 sikkerhetsvurdering"', '"Hunting \\u2014 safety assessment"'),
    ('"Vilttype:"', '"Game type:"'),
    ('"Min. energi:"', '"Min. energy:"'),
    ('"Etisk rekkevidde:"', '"Ethical range:"'),
    ('"Beregn bakstop"', '"Calculate Backstop"'),
    ('"Siktepunkter:"', '"Aim points:"'),
    ('"+ Legg til"', '"+ Add"'),
    ('"\\u2013 Fjern"', '"\\u2013 Remove"'),
    ('"Bakstop-analyse:"', '"Backstop analysis:"'),
    ('"feil"', '"error"'),
    ('"Punkt {n+1}"', '"Point {n+1}"'),
    # Game types
    ('"Elg"', '"Moose"'),
    ('"Hjort"', '"Deer"'),
    ('"Rein"', '"Reindeer"'),
    ('"R\\u00e5dyr"', '"Roe deer"'),
    ('"Villsvin"', '"Boar"'),
    ('"Sm\\u00e5vilt"', '"Small game"'),
]

# ---------------------------------------------------------------------------
# dope_card_panel.py
# ---------------------------------------------------------------------------
DOPE_REPS = [
    ('"DOPE-kort"', '"DOPE Card"'),
    ('"\\U0001f4c4 Skriv ut / PDF"', '"\\U0001f4c4 Print / PDF"'),
    ('"Ukjent ammo"', '"Unknown ammo"'),
    ('"Lagre DOPE-kort som PDF"', '"Save DOPE card as PDF"'),
    ('"\\u2714 Lagret"', '"\\u2714 Saved"'),
    ('"Null:"', '"Zero:"'),
    ('"Advarsler:"', '"Warnings:"'),
]

# ---------------------------------------------------------------------------
# atmosphere_panel.py
# ---------------------------------------------------------------------------
ATM_REPS = [
    ('"Atmosf\\u00e6re"', '"Atmosphere"'),
    ('"Termikk: H\\u00d8YT"', '"Thermal: HIGH"'),
    ('"H\\u00d8YT"', '"HIGH"'),
    ('"MODERAT"', '"MODERATE"'),
    ('"Termikk: {label}"', '"Thermal: {label}"'),
    ('"Atmosf\\xe6re"', '"Atmosphere"'),
]

BASE = "src/ui"
results = {}
for fname, reps in [
    ("ammo_test_window.py", AMMO_REPS),
    ("main_window.py", MAIN_REPS),
    ("field_planning_window.py", FIELD_REPS),
    ("range_tab.py", RANGE_REPS),
    ("hunting_tab.py", HUNTING_REPS),
    ("dope_card_panel.py", DOPE_REPS),
    ("atmosphere_panel.py", ATM_REPS),
]:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        n = translate_file(path, reps)
        results[fname] = n
    else:
        results[fname] = "FILE NOT FOUND"

for fname, n in results.items():
    print(f"{fname}: {n} replacements")
