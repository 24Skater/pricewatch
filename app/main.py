# app/main.py
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Depends,
    Request,
    Form,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db, SessionLocal
from .models import Tracker, PriceHistory, NotificationProfile
from .schemas import TrackerCreate, TrackerOut, ProfileCreate
from .scheduler import start_scheduler
from .scraper import get_price

# Load local environment variables (kept out of Git)
load_dotenv()

app = FastAPI(title="Pricewatch")

# Static & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize DB schema (simple dev path; for prod use Alembic migrations)
Base.metadata.create_all(bind=engine)

# Start background scheduler AFTER DB/session are ready
start_scheduler(SessionLocal)

# ---------------------------
# Public pages
# ---------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    trackers = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    profiles = db.query(NotificationProfile).order_by(NotificationProfile.created_at.desc()).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "trackers": trackers, "profiles": profiles},
    )


@app.post("/trackers", response_class=HTMLResponse)
def create_tracker(
    request: Request,
    url: str = Form(...),
    alert_method: str = Form(...),  # "email" | "sms"
    contact: str = Form(...),       # email or phone, validated below
    selector: str = Form(""),
    name: str = Form(""),
    profile_id: int = Form(0),      # optional NotificationProfile id
    db: Session = Depends(get_db),
):
    # Validate form payload (ensures email/phone match alert method, URL is valid)
    try:
        payload = TrackerCreate(
            url=url,
            alert_method=alert_method,
            contact=contact,
            selector=selector or None,
            name=name or None,
            profile_id=profile_id or None,
        )
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    tracker = Tracker(
        url=str(payload.url),
        alert_method=payload.alert_method,
        contact=payload.contact,
        selector=payload.selector,
        name=payload.name,
    )

    # Attach an optional NotificationProfile (per-user SMTP/SMS settings)
    if payload.profile_id:
        prof = db.query(NotificationProfile).filter(NotificationProfile.id == payload.profile_id).first()
        if not prof:
            raise HTTPException(status_code=400, detail="Profile not found")
        tracker.profile = prof

    # Initial fetch (best effort). If it fails, we still create the tracker so user can adjust selector & poll later.
    price: Optional[float] = None
    currency = "USD"
    title: Optional[str] = None
    try:
        price, currency, title = get_price(tracker.url, tracker.selector)
    except Exception as e:
        print(f"[WARN] Initial fetch failed for {tracker.url}: {e}")

    tracker.currency = currency or "USD"
    if title and not tracker.name:
        tracker.name = title[:200]
    tracker.last_price = price

    db.add(tracker)
    db.commit()
    db.refresh(tracker)

    # Record initial history row if we found a price
    if price is not None:
        db.add(PriceHistory(tracker_id=tracker.id, price=price, delta=None))
        db.commit()

    return RedirectResponse(url=f"/tracker/{tracker.id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/tracker/{tracker_id}", response_class=HTMLResponse)
def tracker_detail(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    history = (
        db.query(PriceHistory)
        .filter(PriceHistory.tracker_id == tracker.id)
        .order_by(PriceHistory.checked_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "tracker.html",
        {"request": request, "tracker": tracker, "history": history},
    )


@app.post("/tracker/{tracker_id}/refresh", response_class=HTMLResponse)
def tracker_refresh(tracker_id: int, db: Session = Depends(get_db)):
    """
    Poll now: immediately re-fetch the price for a tracker and update history if changed.
    """
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")

    try:
        price, currency, _ = get_price(tracker.url, tracker.selector)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch price: {e}")

    if price is None:
        # No change to DB; return a soft error so users can adjust CSS selector
        raise HTTPException(status_code=400, detail="Could not parse a price from the page. Try adding a CSS selector.")

    delta = None if tracker.last_price is None else round(price - tracker.last_price, 2)
    if tracker.last_price is None or abs(price - tracker.last_price) > 1e-6:
        db.add(PriceHistory(tracker_id=tracker.id, price=price, delta=delta))
        tracker.last_price = price
        tracker.currency = tracker.currency or currency or "USD"
        db.add(tracker)
        db.commit()

    # Redirect back to the tracker page to show updated history
    return RedirectResponse(url=f"/tracker/{tracker.id}", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------
# Admin: Notification Profiles
# ---------------------------

@app.get("/admin/profiles", response_class=HTMLResponse)
def profiles_list(request: Request, db: Session = Depends(get_db)):
    profiles = db.query(NotificationProfile).order_by(NotificationProfile.created_at.desc()).all()
    return templates.TemplateResponse("admin/profiles.html", {"request": request, "profiles": profiles})


@app.get("/admin/profiles/new", response_class=HTMLResponse)
def profiles_new(request: Request):
    return templates.TemplateResponse("admin/profile_form.html", {"request": request, "profile": None})


@app.post("/admin/profiles/new", response_class=HTMLResponse)
def profiles_create(
    request: Request,
    name: str = Form(...),
    email_from: str = Form(""),
    smtp_host: str = Form(""),
    smtp_port: int = Form(587),
    smtp_user: str = Form(""),
    smtp_pass: str = Form(""),
    twilio_account_sid: str = Form(""),
    twilio_auth_token: str = Form(""),
    twilio_from_number: str = Form(""),
    db: Session = Depends(get_db),
):
    payload = ProfileCreate(
        name=name,
        email_from=email_from or None,
        smtp_host=smtp_host or None,
        smtp_port=int(smtp_port) if smtp_port else None,
        smtp_user=smtp_user or None,
        smtp_pass=smtp_pass or None,
        twilio_account_sid=twilio_account_sid or None,
        twilio_auth_token=twilio_auth_token or None,
        twilio_from_number=twilio_from_number or None,
    )
    prof = NotificationProfile(**payload.model_dump())
    db.add(prof)
    db.commit()
    return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin/profiles/{profile_id}/edit", response_class=HTMLResponse)
def profiles_edit(profile_id: int, request: Request, db: Session = Depends(get_db)):
    prof = db.query(NotificationProfile).filter(NotificationProfile.id == profile_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    return templates.TemplateResponse("admin/profile_form.html", {"request": request, "profile": prof})


@app.post("/admin/profiles/{profile_id}/edit", response_class=HTMLResponse)
def profiles_update(
    profile_id: int,
    request: Request,
    name: str = Form(...),
    email_from: str = Form(""),
    smtp_host: str = Form(""),
    smtp_port: int = Form(587),
    smtp_user: str = Form(""),
    smtp_pass: str = Form(""),
    twilio_account_sid: str = Form(""),
    twilio_auth_token: str = Form(""),
    twilio_from_number: str = Form(""),
    db: Session = Depends(get_db),
):
    prof = db.query(NotificationProfile).filter(NotificationProfile.id == profile_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    prof.name = name
    prof.email_from = email_from or None
    prof.smtp_host = smtp_host or None
    prof.smtp_port = int(smtp_port) if smtp_port else None
    prof.smtp_user = smtp_user or None
    prof.smtp_pass = smtp_pass or None
    prof.twilio_account_sid = twilio_account_sid or None
    prof.twilio_auth_token = twilio_auth_token or None
    prof.twilio_from_number = twilio_from_number or None

    db.add(prof)
    db.commit()
    return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/profiles/{profile_id}/delete", response_class=HTMLResponse)
def profiles_delete(profile_id: int, db: Session = Depends(get_db)):
    prof = db.query(NotificationProfile).filter(NotificationProfile.id == profile_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Optional: block delete if any tracker uses this profile
    db.delete(prof)
    db.commit()
    return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------
# API (simple read-only helper)
# ---------------------------

@app.get("/api/trackers", response_model=list[TrackerOut])
def api_list_trackers(db: Session = Depends(get_db)):
    items = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    return [TrackerOut.model_validate(i) for i in items]


# ---------------------------
# Optional: health endpoint
# ---------------------------

@app.get("/health")
def health():
    return {"ok": True}
