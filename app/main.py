import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
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

load_dotenv()

app = FastAPI(title="Pricewatch")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)
start_scheduler(SessionLocal)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    trackers = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    profiles = db.query(NotificationProfile).order_by(NotificationProfile.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "trackers": trackers, "profiles": profiles})

@app.post("/trackers", response_class=HTMLResponse)
def create_tracker(
    request: Request,
    url: str = Form(...),
    alert_method: str = Form(...),
    contact: str = Form(...),
    selector: str = Form(""),
    name: str = Form(""),
    profile_id: int = Form(0),
    db: Session = Depends(get_db),
):
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

    t = Tracker(
        url=str(payload.url),
        alert_method=payload.alert_method,
        contact=payload.contact,
        selector=payload.selector,
        name=payload.name,
    )
    if payload.profile_id:
        prof = db.query(NotificationProfile).filter(NotificationProfile.id == payload.profile_id).first()
        if not prof:
            raise HTTPException(status_code=400, detail="Profile not found")
        t.profile = prof

    price: Optional[float] = None
    currency = "USD"
    title: Optional[str] = None
    try:
        price, currency, title = get_price(t.url, t.selector)
    except Exception as e:
        print(f"[WARN] Initial fetch failed for {t.url}: {e}")

    t.currency = currency or "USD"
    if title and not t.name:
        t.name = title[:200]
    t.last_price = price
    db.add(t); db.commit(); db.refresh(t)

    if price is not None:
        db.add(PriceHistory(tracker_id=t.id, price=price, delta=None)); db.commit()

    return RedirectResponse(url=f"/tracker/{t.id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/tracker/{tracker_id}", response_class=HTMLResponse)
def tracker_detail(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")
    history = db.query(PriceHistory).filter(PriceHistory.tracker_id == t.id).order_by(PriceHistory.checked_at.desc()).all()
    return templates.TemplateResponse("tracker.html", {"request": request, "tracker": t, "history": history})

@app.post("/tracker/{tracker_id}/refresh", response_class=HTMLResponse)
def tracker_refresh(tracker_id: int, db: Session = Depends(get_db)):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")
    price, currency, _ = get_price(t.url, t.selector)
    if price is None:
        raise HTTPException(status_code=400, detail="Could not parse a price. Try adding a CSS selector.")
    delta = None if t.last_price is None else round(price - t.last_price, 2)
    if t.last_price is None or abs(price - t.last_price) > 1e-6:
        db.add(PriceHistory(tracker_id=t.id, price=price, delta=delta))
        t.last_price = price
        t.currency = t.currency or (currency or "USD")
        db.add(t); db.commit()
    return RedirectResponse(url=f"/tracker/{t.id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tracker/{tracker_id}/selector", response_class=HTMLResponse)
def tracker_set_selector(tracker_id: int, selector: str = Form(""), db: Session = Depends(get_db)):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")
    t.selector = selector or None
    db.add(t); db.commit()
    return RedirectResponse(url=f"/tracker/{tracker_id}/refresh", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/tracker/{tracker_id}/edit", response_class=HTMLResponse)
def tracker_edit(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")
    profiles = db.query(NotificationProfile).order_by(NotificationProfile.created_at.desc()).all()
    return templates.TemplateResponse("tracker_edit.html", {"request": request, "tracker": t, "profiles": profiles})

@app.post("/tracker/{tracker_id}/edit", response_class=HTMLResponse)
def tracker_update(
    tracker_id: int,
    request: Request,
    url: str = Form(...),
    name: str = Form(""),
    selector: str = Form(""),
    alert_method: str = Form(...),
    contact: str = Form(...),
    profile_id: int = Form(0),
    is_active: bool = Form(False),
    poll_now: int = Form(0),
    db: Session = Depends(get_db),
):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")

    payload = TrackerCreate(
        url=url,
        alert_method=alert_method,
        contact=contact,
        selector=selector or None,
        name=name or None,
        profile_id=profile_id or None,
    )

    t.url = str(payload.url)
    t.name = payload.name
    t.selector = payload.selector
    t.alert_method = payload.alert_method
    t.contact = payload.contact
    t.is_active = bool(is_active)

    if payload.profile_id:
        prof = db.query(NotificationProfile).filter(NotificationProfile.id == payload.profile_id).first()
        if not prof:
            raise HTTPException(status_code=400, detail="Profile not found")
        t.profile = prof
    else:
        t.profile = None

    db.add(t); db.commit(); db.refresh(t)

    if poll_now:
        try:
            price, currency, _ = get_price(t.url, t.selector)
            if price is not None:
                delta = None if t.last_price is None else round(price - t.last_price, 2)
                if t.last_price is None or abs(price - t.last_price) > 1e-6:
                    db.add(PriceHistory(tracker_id=t.id, price=price, delta=delta))
                    t.last_price = price
                    t.currency = t.currency or (currency or "USD")
                    db.add(t); db.commit()
        except Exception as e:
            print(f"[WARN] Poll-after-save failed for {t.id}: {e}")

    return RedirectResponse(url=f"/tracker/{t.id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tracker/{tracker_id}/delete", response_class=HTMLResponse)
def tracker_delete(tracker_id: int, db: Session = Depends(get_db)):
    t = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tracker not found")
    db.query(PriceHistory).filter(PriceHistory.tracker_id == t.id).delete()
    db.delete(t); db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

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
    db.add(prof); db.commit()
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
    db.add(prof); db.commit()
    return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/profiles/{profile_id}/delete", response_class=HTMLResponse)
def profiles_delete(profile_id: int, db: Session = Depends(get_db)):
    prof = db.query(NotificationProfile).filter(NotificationProfile.id == profile_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(prof); db.commit()
    return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/api/trackers", response_model=list[TrackerOut])
def api_list_trackers(db: Session = Depends(get_db)):
    items = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    return [TrackerOut.model_validate(i) for i in items]

@app.get("/health")
def health():
    return {"ok": True}
