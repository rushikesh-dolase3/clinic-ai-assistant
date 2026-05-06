from sqlalchemy import Column, Integer, String
from app.database import Base

# Doctor Table
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    name = Column(String)

# Appointment Table
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String)
    phone = Column(String)
    doctor = Column(String)
    date = Column(String)
    time = Column(String)