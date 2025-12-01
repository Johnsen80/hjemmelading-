# Standarder for kaliber: SAAMI, CIP, NATO
# Denne modulen gir oversikt og felter for å lagre kaliberstandarder i databasen

from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CaliberStandard(Base):
    __tablename__ = 'caliber_standard'
    id = Column(Integer, primary_key=True)
    caliber_name = Column(String)
    saami_spec = Column(String)
    cip_spec = Column(String)
    nato_spec = Column(String)
    max_pressure_saami = Column(Float)
    max_pressure_cip = Column(Float)
    max_pressure_nato = Column(Float)
    notes = Column(String)
    # ...eventuelt flere felter for dimensjoner, patronlengde, hylsevolum, etc.

# Eksempel på bruk:
# caliber = CaliberStandard(
#     caliber_name=".308 Winchester",
#     saami_spec="SAAMI: .308 Win, Max Pressure: 62,000 psi",
#     cip_spec="CIP: .308 Win, Max Pressure: 415 MPa",
#     nato_spec="NATO: 7.62x51mm, Max Pressure: 60,191 psi",
#     max_pressure_saami=62000,
#     max_pressure_cip=415,
#     max_pressure_nato=60191,
#     notes="Vanlig jakt- og militærkaliber."
# )
