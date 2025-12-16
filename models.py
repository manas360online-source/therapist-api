from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class Therapist(Base):
    __tablename__ = "therapists"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    specialization = Column(String, nullable=True)
    bio = Column(Text, nullable=True)

    leads = relationship("Lead", back_populates="therapist")
    sessions = relationship("Session", back_populates="therapist")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"))
    patient_name = Column(String, nullable=False)
    issue = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    purchased = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    therapist = relationship("Therapist", back_populates="leads")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"))
    patient_name = Column(String, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled
    fee = Column(Float, default=0.0)
    notes_encrypted = Column(Text, nullable=True)

    therapist = relationship("Therapist", back_populates="sessions")
