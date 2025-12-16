from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TherapistCreate(BaseModel):
    full_name: str
    email: str
    specialization: Optional[str] = None
    bio: Optional[str] = None

class TherapistOut(BaseModel):
    id: int
    full_name: str
    email: str
    specialization: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        orm_mode = True

class LeadOut(BaseModel):
    id: int
    patient_name: str
    issue: Optional[str] = None
    price: float
    purchased: bool
    created_at: datetime

    class Config:
        orm_mode = True

class SessionOut(BaseModel):
    id: int
    patient_name: str
    scheduled_for: datetime
    status: str
    fee: float

    class Config:
        orm_mode = True

class SessionUpdate(BaseModel):
    status: Optional[str] = None
    fee: Optional[float] = None

class SessionNotesCreate(BaseModel):
    notes: str

class EarningsSummary(BaseModel):
    total_earnings: float
    from_sessions: float
    spent_on_leads: float
    net_earnings: float
