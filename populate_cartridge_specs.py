"""
SAAMI, CIP og NATO Cartridge Specifications
Data fra offisielle standarder for sikkerhet og toleranser
"""

from src.database.database import Database


def populate_cartridge_specs():
    """Populer database med offisielle kaliber-spesifikasjoner"""

    db = Database()

    # Sjekk om tabell eksisterer
    db.execute_query(
        """
        CREATE TABLE IF NOT EXISTS cartridge_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cartridge_name TEXT NOT NULL UNIQUE,
            standard_body TEXT NOT NULL,  -- 'SAAMI', 'CIP', 'NATO'
            max_pressure_psi INTEGER,
            max_pressure_bar INTEGER,
            max_avg_pressure_psi INTEGER,  -- MAP (Maximum Average Pressure)
            proof_pressure_psi INTEGER,     -- Proof test pressure
            case_length_inches REAL,
            case_length_mm REAL,
            case_capacity_grains_h2o REAL,  -- Water capacity
            max_coal_inches REAL,           -- Maximum cartridge overall length
            max_coal_mm REAL,
            rim_diameter_inches REAL,
            rim_diameter_mm REAL,
            case_head_diameter_inches REAL,
            case_head_diameter_mm REAL,
            neck_diameter_inches REAL,
            neck_diameter_mm REAL,
            shoulder_angle_deg REAL,
            saami_drawing_number TEXT,
            notes TEXT,
            date_adopted TEXT,
            date_updated TEXT
        )
    """
    )

    print("📋 Legger til SAAMI/CIP/NATO standarder...")

    # Data fra offisielle kilder
    cartridge_data = [
        # SAAMI Standards - Mest brukte kalibere
        {
            "cartridge_name": "6.5 Creedmoor",
            "standard_body": "SAAMI",
            "max_pressure_psi": 62000,
            "max_pressure_bar": 4275,
            "max_avg_pressure_psi": 62000,  # MAP
            "proof_pressure_psi": 77500,  # 125% av MAP
            "case_length_inches": 1.920,
            "case_length_mm": 48.77,
            "case_capacity_grains_h2o": 52.5,  # Lapua brass
            "max_coal_inches": 2.825,
            "max_coal_mm": 71.755,
            "rim_diameter_inches": 0.473,
            "rim_diameter_mm": 12.01,
            "case_head_diameter_inches": 0.470,
            "case_head_diameter_mm": 11.94,
            "neck_diameter_inches": 0.295,
            "neck_diameter_mm": 7.49,
            "shoulder_angle_deg": 30.0,
            "saami_drawing_number": "Z223-15",
            "notes": "Modern short-action precision cartridge. Very popular for competition and hunting.",
            "date_adopted": "2007",
            "date_updated": "2015",
        },
        {
            "cartridge_name": ".308 Winchester",
            "standard_body": "SAAMI",
            "max_pressure_psi": 62000,
            "max_pressure_bar": 4275,
            "max_avg_pressure_psi": 62000,
            "proof_pressure_psi": 77500,
            "case_length_inches": 2.015,
            "case_length_mm": 51.18,
            "case_capacity_grains_h2o": 56.0,  # Winchester brass
            "max_coal_inches": 2.810,
            "max_coal_mm": 71.37,
            "rim_diameter_inches": 0.473,
            "rim_diameter_mm": 12.01,
            "case_head_diameter_inches": 0.470,
            "case_head_diameter_mm": 11.94,
            "neck_diameter_inches": 0.345,
            "neck_diameter_mm": 8.76,
            "shoulder_angle_deg": 20.0,
            "saami_drawing_number": "Z223-4",
            "notes": "Most popular .30 caliber worldwide. Military equivalent: 7.62x51mm NATO.",
            "date_adopted": "1952",
            "date_updated": "2012",
        },
        {
            "cartridge_name": "7.62x51mm NATO",
            "standard_body": "NATO",
            "max_pressure_psi": 62366,  # NATO spec: 430 MPa
            "max_pressure_bar": 4300,
            "max_avg_pressure_psi": 60191,  # NATO MAP
            "proof_pressure_psi": 70000,
            "case_length_inches": 2.015,
            "case_length_mm": 51.18,
            "case_capacity_grains_h2o": 54.0,  # Mil brass (thicker)
            "max_coal_inches": 2.800,  # NATO max
            "max_coal_mm": 71.12,
            "rim_diameter_inches": 0.473,
            "rim_diameter_mm": 12.01,
            "case_head_diameter_inches": 0.470,
            "case_head_diameter_mm": 11.94,
            "neck_diameter_inches": 0.345,
            "neck_diameter_mm": 8.76,
            "shoulder_angle_deg": 20.0,
            "saami_drawing_number": "NATO STANAG 4383",
            "notes": "Military version of .308 Win. Thicker brass, lower capacity. Semi-auto safe.",
            "date_adopted": "1954",
            "date_updated": "2010",
        },
        {
            "cartridge_name": ".223 Remington",
            "standard_body": "SAAMI",
            "max_pressure_psi": 55000,
            "max_pressure_bar": 3792,
            "max_avg_pressure_psi": 55000,
            "proof_pressure_psi": 68750,
            "case_length_inches": 1.760,
            "case_length_mm": 44.70,
            "case_capacity_grains_h2o": 28.5,  # Lapua brass
            "max_coal_inches": 2.260,
            "max_coal_mm": 57.40,
            "rim_diameter_inches": 0.378,
            "rim_diameter_mm": 9.60,
            "case_head_diameter_inches": 0.376,
            "case_head_diameter_mm": 9.55,
            "neck_diameter_inches": 0.253,
            "neck_diameter_mm": 6.43,
            "shoulder_angle_deg": 23.0,
            "saami_drawing_number": "Z223-11",
            "notes": "Commercial version. LONGER THROAT than 5.56 NATO. NOT safe for all 5.56 loads!",
            "date_adopted": "1964",
            "date_updated": "2015",
        },
        {
            "cartridge_name": "5.56x45mm NATO",
            "standard_body": "NATO",
            "max_pressure_psi": 62366,  # NATO: 430 MPa (høyere enn .223!)
            "max_pressure_bar": 4300,
            "max_avg_pressure_psi": 58000,
            "proof_pressure_psi": 75000,
            "case_length_inches": 1.760,
            "case_length_mm": 44.70,
            "case_capacity_grains_h2o": 28.0,  # Mil brass
            "max_coal_inches": 2.260,
            "max_coal_mm": 57.40,
            "rim_diameter_inches": 0.378,
            "rim_diameter_mm": 9.60,
            "case_head_diameter_inches": 0.376,
            "case_head_diameter_mm": 9.55,
            "neck_diameter_inches": 0.253,
            "neck_diameter_mm": 6.43,
            "shoulder_angle_deg": 23.0,
            "saami_drawing_number": "NATO STANAG 4172",
            "notes": "Military version. SHORTER THROAT! Higher pressure than .223 Rem. Safe in 5.56 chambers.",
            "date_adopted": "1980",
            "date_updated": "2012",
        },
        {
            "cartridge_name": ".30-06 Springfield",
            "standard_body": "SAAMI",
            "max_pressure_psi": 60000,
            "max_pressure_bar": 4137,
            "max_avg_pressure_psi": 60000,
            "proof_pressure_psi": 75000,
            "case_length_inches": 2.494,
            "case_length_mm": 63.35,
            "case_capacity_grains_h2o": 68.0,
            "max_coal_inches": 3.340,
            "max_coal_mm": 84.84,
            "rim_diameter_inches": 0.473,
            "rim_diameter_mm": 12.01,
            "case_head_diameter_inches": 0.470,
            "case_head_diameter_mm": 11.94,
            "neck_diameter_inches": 0.340,
            "neck_diameter_mm": 8.64,
            "shoulder_angle_deg": 17.5,
            "saami_drawing_number": "Z223-2",
            "notes": "Classic full-length cartridge. Excellent versatility. 150-220gr bullets.",
            "date_adopted": "1906",
            "date_updated": "2010",
        },
        {
            "cartridge_name": "6mm Creedmoor",
            "standard_body": "SAAMI",
            "max_pressure_psi": 62000,
            "max_pressure_bar": 4275,
            "max_avg_pressure_psi": 62000,
            "proof_pressure_psi": 77500,
            "case_length_inches": 1.920,
            "case_length_mm": 48.77,
            "case_capacity_grains_h2o": 53.5,  # Slightly more than 6.5 CM (smaller bullet)
            "max_coal_inches": 2.825,
            "max_coal_mm": 71.755,
            "rim_diameter_inches": 0.473,
            "rim_diameter_mm": 12.01,
            "case_head_diameter_inches": 0.470,
            "case_head_diameter_mm": 11.94,
            "neck_diameter_inches": 0.276,
            "neck_diameter_mm": 7.01,
            "shoulder_angle_deg": 30.0,
            "saami_drawing_number": "Z223-17",
            "notes": "Necked-down 6.5 Creedmoor. Excellent for PRS competition. 105-115gr bullets.",
            "date_adopted": "2017",
            "date_updated": "2018",
        },
        {
            "cartridge_name": "6.5x55 Swedish",
            "standard_body": "CIP",
            "max_pressure_psi": 55114,  # CIP: 380 MPa
            "max_pressure_bar": 3800,
            "max_avg_pressure_psi": 51487,  # CIP MAP (conservative for old actions)
            "proof_pressure_psi": 66000,
            "case_length_inches": 2.165,
            "case_length_mm": 55.0,
            "case_capacity_grains_h2o": 60.0,
            "max_coal_inches": 3.150,
            "max_coal_mm": 80.0,
            "rim_diameter_inches": 0.480,
            "rim_diameter_mm": 12.20,
            "case_head_diameter_inches": 0.480,
            "case_head_diameter_mm": 12.20,
            "neck_diameter_inches": 0.296,
            "neck_diameter_mm": 7.52,
            "shoulder_angle_deg": 25.0,
            "saami_drawing_number": "CIP 131",
            "notes": "European classic. CIP pressure conservative for old rifles. Modern actions can handle more.",
            "date_adopted": "1894",
            "date_updated": "2008",
        },
        {
            "cartridge_name": ".300 Winchester Magnum",
            "standard_body": "SAAMI",
            "max_pressure_psi": 64000,
            "max_pressure_bar": 4413,
            "max_avg_pressure_psi": 64000,
            "proof_pressure_psi": 80000,
            "case_length_inches": 2.620,
            "case_length_mm": 66.55,
            "case_capacity_grains_h2o": 93.0,  # Large capacity magnum
            "max_coal_inches": 3.340,
            "max_coal_mm": 84.84,
            "rim_diameter_inches": 0.532,
            "rim_diameter_mm": 13.51,
            "case_head_diameter_inches": 0.532,
            "case_head_diameter_mm": 13.51,
            "neck_diameter_inches": 0.339,
            "neck_diameter_mm": 8.61,
            "shoulder_angle_deg": 25.0,
            "saami_drawing_number": "Z223-5",
            "notes": "Powerful magnum. Requires slow powder and careful load development. 180-220gr bullets.",
            "date_adopted": "1963",
            "date_updated": "2012",
        },
        {
            "cartridge_name": "6.5 PRC",
            "standard_body": "SAAMI",
            "max_pressure_psi": 65000,
            "max_pressure_bar": 4482,
            "max_avg_pressure_psi": 65000,
            "proof_pressure_psi": 81250,
            "case_length_inches": 2.030,
            "case_length_mm": 51.56,
            "case_capacity_grains_h2o": 66.0,  # Similar to .270 Win
            "max_coal_inches": 2.955,
            "max_coal_mm": 75.06,
            "rim_diameter_inches": 0.532,
            "rim_diameter_mm": 13.51,
            "case_head_diameter_inches": 0.532,
            "case_head_diameter_mm": 13.51,
            "neck_diameter_inches": 0.295,
            "neck_diameter_mm": 7.49,
            "shoulder_angle_deg": 30.0,
            "saami_drawing_number": "Z223-21",
            "notes": "Modern precision magnum. Optimized for heavy 6.5mm bullets (140-156gr). High BC.",
            "date_adopted": "2018",
            "date_updated": "2019",
        },
    ]

    # Innsett data
    for spec in cartridge_data:
        db.execute_query(
            """
            INSERT OR REPLACE INTO cartridge_specs (
                cartridge_name, standard_body, max_pressure_psi, max_pressure_bar,
                max_avg_pressure_psi, proof_pressure_psi, case_length_inches, case_length_mm,
                case_capacity_grains_h2o, max_coal_inches, max_coal_mm,
                rim_diameter_inches, rim_diameter_mm, case_head_diameter_inches,
                case_head_diameter_mm, neck_diameter_inches, neck_diameter_mm,
                shoulder_angle_deg, saami_drawing_number, notes, date_adopted, date_updated
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """,
            (
                spec["cartridge_name"],
                spec["standard_body"],
                spec["max_pressure_psi"],
                spec["max_pressure_bar"],
                spec["max_avg_pressure_psi"],
                spec["proof_pressure_psi"],
                spec["case_length_inches"],
                spec["case_length_mm"],
                spec["case_capacity_grains_h2o"],
                spec["max_coal_inches"],
                spec["max_coal_mm"],
                spec["rim_diameter_inches"],
                spec["rim_diameter_mm"],
                spec["case_head_diameter_inches"],
                spec["case_head_diameter_mm"],
                spec["neck_diameter_inches"],
                spec["neck_diameter_mm"],
                spec["shoulder_angle_deg"],
                spec["saami_drawing_number"],
                spec["notes"],
                spec["date_adopted"],
                spec["date_updated"],
            ),
        )

    print(f"✅ Lagt til {len(cartridge_data)} kaliber-spesifikasjoner")
    print("\n📊 SAAMI/CIP/NATO standarder:")
    for spec in cartridge_data:
        print(
            f"  • {spec['cartridge_name']}: {spec['max_pressure_psi']:,} PSI max ({spec['standard_body']})"
        )

    db.close()
    print("\n✅ Cartridge specifications database populert!")


if __name__ == "__main__":
    populate_cartridge_specs()
