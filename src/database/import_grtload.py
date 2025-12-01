import os
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from .database import PowderData

def import_grtload_xml(file_path: str, db_session: Session):
    """
    Importer kruttdata fra GRT .grtload XML-fil til PowderData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    tree = ET.parse(file_path)
    root = tree.getroot()
    for powder in root.findall('.//Powder'):
        name = powder.findtext('Name')
        manufacturer = powder.findtext('Manufacturer')
        type_ = powder.findtext('Type')
        burn_rate = powder.findtext('BurnRate')
        energy_density = powder.findtext('EnergyDensity')
        charge_min = powder.findtext('RecommendedChargeMin')
        charge_max = powder.findtext('RecommendedChargeMax')
        reference = powder.findtext('Reference')
        db_powder = PowderData(
            name=name,
            manufacturer=manufacturer,
            type=type_,
            burn_rate=float(burn_rate) if burn_rate else None,
            energy_density=float(energy_density) if energy_density else None,
            recommended_charge_min=float(charge_min) if charge_min else None,
            recommended_charge_max=float(charge_max) if charge_max else None,
            reference=reference
        )
        db_session.add(db_powder)
    db_session.commit()
    print(f"Importert kruttdata fra {file_path}")

# Eksempel på bruk:
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# engine = create_engine('sqlite:///hjemmelading.db')
# Session = sessionmaker(bind=engine)
# session = Session()
# import_grtload_xml('POWDER-MEASURE-TEMPLATE.grtload', session)
