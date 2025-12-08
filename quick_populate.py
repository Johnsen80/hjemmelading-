"""
Quick Database Populator - Legger til minimum data for testing
"""

import sqlite3

conn = sqlite3.connect("data/reloading.db")
c = conn.cursor()

print("Adding bullets...")
bullets = [
    # Match bullets from major manufacturers
    (
        "Lapua Scenar 139gr",
        "Lapua",
        "6.5mm",
        139,
        0.615,
        0.290,
        "Match",
        "Finnish precision, very consistent",
    ),
    (
        "Berger 140gr Hybrid",
        "Berger",
        "6.5mm",
        140,
        0.618,
        0.287,
        "Match",
        "Forgiving seating depth",
    ),
    (
        "Sierra MatchKing 142gr",
        "Sierra",
        "6.5mm",
        142,
        0.626,
        0.295,
        "Match",
        "6.5 CM gold standard",
    ),
    (
        "Norma Golden Target 140gr",
        "Norma",
        "6.5mm",
        140,
        0.585,
        0.295,
        "Match",
        "Swedish premium match",
    ),
    (
        "Hornady ELD-M 147gr",
        "Hornady",
        "6.5mm",
        147,
        0.697,
        0.351,
        "Match",
        "High BC, heat shield tip",
    ),
    (
        "Sierra MatchKing 168gr",
        "Sierra",
        "7.62mm",
        168,
        0.462,
        0.231,
        "Match",
        ".308 Win classic",
    ),
    (
        "Berger 175gr OTM",
        "Berger",
        "7.62mm",
        175,
        0.505,
        0.243,
        "Match",
        "Military sniper choice",
    ),
    (
        "Sierra MatchKing 77gr",
        "Sierra",
        "5.56mm",
        77,
        0.372,
        0.196,
        "Match",
        "AR-15 service rifle std",
    ),
    # Hunting bullets
    (
        "Lapua MEGA 140gr",
        "Lapua",
        "6.5mm",
        140,
        0.462,
        0.231,
        "Hunting",
        "Soft point, Scandinavian favorite",
    ),
    (
        "Barnes TTSX 168gr",
        "Barnes",
        "7.62mm",
        168,
        0.470,
        0.235,
        "Hunting",
        "100% copper, deep penetration",
    ),
]

for name, mfg, cal, weight, bc_g1, bc_g7, btype, notes in bullets:
    c.execute(
        "INSERT INTO bullets (name, manufacturer, caliber, weight_grains, bc_g1, bc_g7, bullet_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, mfg, cal, weight, bc_g1, bc_g7, btype, notes),
    )

print(f"Added {len(bullets)} bullets")

print("Adding powder...")
powders = [
    ("H4350", "Hodgdon", "Extruded", 0.52, "6.5 Creedmoor favorite, temp stable"),
    ("Varget", "Hodgdon", "Extruded", 0.53, ".308 Win king, very versatile"),
    ("RL16", "Alliant", "Extruded", 0.50, "Modern, temp stable"),
    ("N140", "Vihtavuori", "Extruded", 0.910, "Versatile .223 to .375 H&H, very clean"),
    ("N160", "Vihtavuori", "Extruded", 0.920, "6.5-284, .270 Win, temp stable"),
    ("N540", "Vihtavuori", "Extruded", 0.940, "High energy for 6.5 CM, .308 Win"),
    ("N555", "Vihtavuori", "Extruded", 0.900, "Developed for 6.5 Creedmoor comp"),
    ("IMR 4064", "IMR", "Extruded", 0.54, "Classic .308 powder"),
]

for name, mfg, ptype, dens, notes in powders:
    c.execute(
        "INSERT INTO powder (name, manufacturer, type, density, notes) VALUES (?, ?, ?, ?, ?)",
        (name, mfg, ptype, dens, notes),
    )

print(f"Added {len(powders)} powders")

print("Adding primers...")
primers = [
    ("CCI BR-2", "Large Rifle Benchrest", "CCI", "Benchrest primer"),
    ("Federal 210M", "Large Rifle Match", "Federal", "Match standard"),
    ("CCI 200", "Large Rifle", "CCI", "Standard LR"),
    ("CCI 450", "Small Rifle Magnum", "CCI", "For .223"),
    ("Federal 205M", "Small Rifle Match", "Federal", "Match SR"),
]

for name, ptype, mfg, notes in primers:
    c.execute(
        "INSERT INTO primers (name, type, manufacturer, notes) VALUES (?, ?, ?, ?)",
        (name, ptype, mfg, notes),
    )

print(f"Added {len(primers)} primers")

conn.commit()
conn.close()
print("\n✅ Database populated! Test Smart Loading Wizard now!")
