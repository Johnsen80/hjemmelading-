# Eksempeldata for vanlige kalibre med SAAMI, CIP og NATO-standarder
from .caliber_standard import CaliberStandard

def get_example_caliber_standards():
    return [
        CaliberStandard(
            caliber_name=".308 Winchester",
            saami_spec="SAAMI: .308 Win, Max Pressure: 62,000 psi",
            cip_spec="CIP: .308 Win, Max Pressure: 415 MPa",
            nato_spec="NATO: 7.62x51mm, Max Pressure: 60,191 psi",
            max_pressure_saami=62000,
            max_pressure_cip=415,
            max_pressure_nato=60191,
            notes="Vanlig jakt- og militærkaliber."
        ),
        CaliberStandard(
            caliber_name=".223 Remington",
            saami_spec="SAAMI: .223 Rem, Max Pressure: 55,000 psi",
            cip_spec="CIP: .223 Rem, Max Pressure: 430 MPa",
            nato_spec="NATO: 5.56x45mm, Max Pressure: 62,366 psi",
            max_pressure_saami=55000,
            max_pressure_cip=430,
            max_pressure_nato=62366,
            notes="Populær for jakt og sport."
        ),
        CaliberStandard(
            caliber_name="6.5 Creedmoor",
            saami_spec="SAAMI: 6.5 Creedmoor, Max Pressure: 62,000 psi",
            cip_spec="CIP: 6.5 Creedmoor, Max Pressure: 435 MPa",
            nato_spec="-",
            max_pressure_saami=62000,
            max_pressure_cip=435,
            max_pressure_nato=None,
            notes="Moderne langholdskaliber."
        ),
        CaliberStandard(
            caliber_name=".30-06 Springfield",
            saami_spec="SAAMI: .30-06 Sprg, Max Pressure: 60,000 psi",
            cip_spec="CIP: .30-06 Sprg, Max Pressure: 405 MPa",
            nato_spec="-",
            max_pressure_saami=60000,
            max_pressure_cip=405,
            max_pressure_nato=None,
            notes="Klassisk jaktkaliber."
        ),
        CaliberStandard(
            caliber_name="9mm Luger",
            saami_spec="SAAMI: 9mm Luger, Max Pressure: 35,000 psi",
            cip_spec="CIP: 9mm Luger, Max Pressure: 235 MPa",
            nato_spec="NATO: 9x19mm, Max Pressure: 36,500 psi",
            max_pressure_saami=35000,
            max_pressure_cip=235,
            max_pressure_nato=36500,
            notes="Standard pistolkaliber."
        ),
        CaliberStandard(
            caliber_name=".338 Lapua Magnum",
            saami_spec="SAAMI: .338 Lapua Mag, Max Pressure: 60,000 psi",
            cip_spec="CIP: .338 Lapua Mag, Max Pressure: 420 MPa",
            nato_spec="-",
            max_pressure_saami=60000,
            max_pressure_cip=420,
            max_pressure_nato=None,
            notes="Langhold og militær presisjonskaliber."
        ),
        # ...flere kalibre kan legges til her...
    ]

# Eksempel på bruk:
# for cal in get_example_caliber_standards():
#     session.add(cal)
# session.commit()
