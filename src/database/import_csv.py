import csv
import os

from sqlalchemy.orm import Session

from .database import BulletData, PowderData


def import_powder_csv(file_path: str, db_session: Session):
    """
    Importer kruttdata fra CSV-fil til PowderData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            db_powder = PowderData(
                name=row.get("Name"),
                manufacturer=row.get("Manufacturer"),
                type=row.get("Type"),
                burn_rate=(
                    float(row.get("BurnRate", 0)) if row.get("BurnRate") else None
                ),
                energy_density=(
                    float(row.get("EnergyDensity", 0))
                    if row.get("EnergyDensity")
                    else None
                ),
                recommended_charge_min=(
                    float(row.get("RecommendedChargeMin", 0))
                    if row.get("RecommendedChargeMin")
                    else None
                ),
                recommended_charge_max=(
                    float(row.get("RecommendedChargeMax", 0))
                    if row.get("RecommendedChargeMax")
                    else None
                ),
                reference=row.get("Reference"),
            )
            db_session.add(db_powder)
    db_session.commit()
    print(f"Importert kruttdata fra {file_path}")


def import_bullet_csv(file_path: str, db_session: Session):
    """
    Importer kuledata fra CSV-fil til BulletData-tabellen.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Finner ikke fil: {file_path}")
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            db_bullet = BulletData(
                name=row.get("Name"),
                manufacturer=row.get("Manufacturer"),
                diameter=float(row.get("Diameter", 0)) if row.get("Diameter") else None,
                weight=float(row.get("Weight", 0)) if row.get("Weight") else None,
                bc=float(row.get("BC", 0)) if row.get("BC") else None,
                type=row.get("Type"),
                length=float(row.get("Length", 0)) if row.get("Length") else None,
                recommended_twist=(
                    float(row.get("RecommendedTwist", 0))
                    if row.get("RecommendedTwist")
                    else None
                ),
                reference=row.get("Reference"),
            )
            db_session.add(db_bullet)
    db_session.commit()
    print(f"Importert kuledata fra {file_path}")


# Eksempel på bruk:
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# engine = create_engine('sqlite:///hjemmelading.db')
# Session = sessionmaker(bind=engine)
# session = Session()
# import_powder_csv('powder_data.csv', session)
# import_bullet_csv('bullet_data.csv', session)
