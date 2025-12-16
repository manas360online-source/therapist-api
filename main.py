from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from typing import List
from pathlib import Path
from datetime import datetime, timedelta

from database import Base, engine, get_db
from models import Therapist, Lead, Session
from schemas import (
    TherapistCreate,
    TherapistOut,
    LeadOut,
    SessionOut,
    SessionUpdate,
    SessionNotesCreate,
    EarningsSummary,
)
from security import encrypt_text

# Create database tables
Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR.mkdir(exist_ok=True)
FRONTEND_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Therapist Practice Management API",
    version="1.0.0",
    description="APIs to help therapists manage profiles, leads, sessions, and earnings.",
)

# CORS (if you later serve frontend separately)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.get("/", include_in_schema=False)
def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Therapist API running"}

# Helper: get "current therapist". For demo, always therapist with id=1.
def get_current_therapist(db: DBSession) -> Therapist:
    therapist = db.query(Therapist).filter(Therapist.id == 1).first()
    if not therapist:
        therapist = Therapist(
            id=1,
            full_name="Demo Therapist",
            email="therapist@example.com",
            specialization="General",
            bio="This is a demo therapist profile.",
        )
        db.add(therapist)
        db.commit()
        db.refresh(therapist)
        # also seed some leads & sessions
        seed_sample_data(db, therapist.id)
    return therapist

def seed_sample_data(db: DBSession, therapist_id: int):
    # Only seed if none exist
    if db.query(Lead).filter(Lead.therapist_id == therapist_id).count() == 0:
        leads = [
            Lead(
                therapist_id=therapist_id,
                patient_name="Alice",
                issue="Anxiety & stress",
                price=20.0,
                purchased=False,
            ),
            Lead(
                therapist_id=therapist_id,
                patient_name="Bob",
                issue="Work burnout",
                price=25.0,
                purchased=False,
            ),
        ]
        db.add_all(leads)

    if db.query(Session).filter(Session.therapist_id == therapist_id).count() == 0:
        now = datetime.utcnow()
        sessions = [
            Session(
                therapist_id=therapist_id,
                patient_name="Charlie",
                scheduled_for=now + timedelta(days=1),
                status="scheduled",
                fee=100.0,
            ),
            Session(
                therapist_id=therapist_id,
                patient_name="Dana",
                scheduled_for=now - timedelta(days=1),
                status="completed",
                fee=120.0,
            ),
        ]
        db.add_all(sessions)
    db.commit()

# --------- API ENDPOINTS ---------

# 1. Create therapist profile
@app.post("/api/v1/therapists/profile", response_model=TherapistOut)
def create_therapist_profile(payload: TherapistCreate, db: DBSession = Depends(get_db)):
    therapist = db.query(Therapist).filter(Therapist.email == payload.email).first()
    if therapist:
        # Update existing
        therapist.full_name = payload.full_name
        therapist.specialization = payload.specialization
        therapist.bio = payload.bio
    else:
        therapist = Therapist(
            full_name=payload.full_name,
            email=payload.email,
            specialization=payload.specialization,
            bio=payload.bio,
        )
        db.add(therapist)
    db.commit()
    db.refresh(therapist)
    return therapist

# 2. Get current therapist profile
@app.get("/api/v1/therapists/me/profile", response_model=TherapistOut)
def get_my_profile(db: DBSession = Depends(get_db)):
    therapist = get_current_therapist(db)
    return therapist

# 3. Upload therapist documents ("S3" simulated as local uploads folder)
@app.post("/api/v1/therapists/me/documents")
async def upload_document(
    file: UploadFile = File(...), db: DBSession = Depends(get_db)
):
    therapist = get_current_therapist(db)
    # Store file under uploads/therapist_<id>/
    therapist_dir = UPLOAD_DIR / f"therapist_{therapist.id}"
    therapist_dir.mkdir(exist_ok=True)
    dest = therapist_dir / file.filename

    with dest.open("wb") as f:
        content = await file.read()
        f.write(content)

    # In real life we'd upload to S3 and store the URL
    return {
        "message": "File uploaded successfully to mock S3",
        "file_name": file.filename,
        "path": str(dest),
    }

# 4. List leads
@app.get("/api/v1/therapists/me/leads", response_model=List[LeadOut])
def list_leads(db: DBSession = Depends(get_db)):
    therapist = get_current_therapist(db)
    leads = (
        db.query(Lead)
        .filter(Lead.therapist_id == therapist.id)
        .order_by(Lead.created_at.desc())
        .all()
    )
    return leads

# 5. Purchase a lead
@app.post("/api/v1/therapists/me/leads/{lead_id}/purchase")
def purchase_lead(lead_id: int, db: DBSession = Depends(get_db)):
    therapist = get_current_therapist(db)
    lead = (
        db.query(Lead)
        .filter(Lead.therapist_id == therapist.id, Lead.id == lead_id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.purchased:
        return {"message": "Lead already purchased"}

    lead.purchased = True
    db.commit()
    return {"message": "Lead purchased successfully", "lead_id": lead.id}

# 6. List sessions
@app.get("/api/v1/therapists/me/sessions", response_model=List[SessionOut])
def list_sessions(db: DBSession = Depends(get_db)):
    therapist = get_current_therapist(db)
    sessions = (
        db.query(Session)
        .filter(Session.therapist_id == therapist.id)
        .order_by(Session.scheduled_for.desc())
        .all()
    )
    return sessions

# 7. Update a session (status/fee)
@app.patch("/api/v1/therapists/me/sessions/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int, payload: SessionUpdate, db: DBSession = Depends(get_db)
):
    therapist = get_current_therapist(db)
    session = (
        db.query(Session)
        .filter(Session.therapist_id == therapist.id, Session.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if payload.status is not None:
        session.status = payload.status
    if payload.fee is not None:
        session.fee = payload.fee

    db.commit()
    db.refresh(session)
    return session

# 8. Add encrypted session notes
@app.post("/api/v1/therapists/me/sessions/{session_id}/notes")
def add_session_notes(
    session_id: int, payload: SessionNotesCreate, db: DBSession = Depends(get_db)
):
    therapist = get_current_therapist(db)
    session = (
        db.query(Session)
        .filter(Session.therapist_id == therapist.id, Session.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.notes_encrypted = encrypt_text(payload.notes)
    db.commit()
    return {"message": "Session notes stored in encrypted form"}

# 9. Earnings summary
@app.get("/api/v1/therapists/me/earnings", response_model=EarningsSummary)
def get_earnings(db: DBSession = Depends(get_db)):
    therapist = get_current_therapist(db)

    sessions = (
        db.query(Session)
        .filter(Session.therapist_id == therapist.id, Session.status == "completed")
        .all()
    )
    from_sessions = sum(s.fee for s in sessions)

    leads = (
        db.query(Lead)
        .filter(Lead.therapist_id == therapist.id, Lead.purchased == True)
        .all()
    )
    spent_on_leads = sum(l.price for l in leads)

    total_earnings = from_sessions
    net_earnings = total_earnings - spent_on_leads

    return EarningsSummary(
        total_earnings=total_earnings,
        from_sessions=from_sessions,
        spent_on_leads=spent_on_leads,
        net_earnings=net_earnings,
    )
