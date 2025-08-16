import os
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Tracker, PriceHistory
from .schemas import TrackerCreate, TrackerOut
from .scheduler import start_scheduler
from .scraper import get_price

app = FastAPI(title="Pricewatch")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)

from .database import SessionLocal
start_scheduler(SessionLocal)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    trackers = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "trackers": trackers})

@app.post("/trackers", response_class=HTMLResponse)
def create_tracker(
    request: Request,
    url: str = Form(...),
    alert_method: str = Form(...),
    contact: str = Form(...),
    selector: str = Form(""),
    name: str = Form(""),
    db: Session = Depends(get_db),
):
    payload = TrackerCreate(url=url, alert_method=alert_method, contact=contact, selector=selector or None, name=name or None)
    tracker = Tracker(url=str(payload.url), alert_method=payload.alert_method, contact=payload.contact, selector=payload.selector, name=payload.name)
    try:
        price, currency, title = get_price(tracker.url, tracker.selector)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Initial fetch failed: {e}")
    tracker.currency = currency or "USD"
    if title and not tracker.name:
        tracker.name = title[:200]
    tracker.last_price = price
    db.add(tracker)
    db.commit()
    db.refresh(tracker)
    if price is not None:
        ph = PriceHistory(tracker_id=tracker.id, price=price, delta=None)
        db.add(ph)
        db.commit()

    return RedirectResponse(url=f"/tracker/{tracker.id}", status_code=303)

@app.get("/tracker/{tracker_id}", response_class=HTMLResponse)
def tracker_detail(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).first()
    if not tracker:
        raise HTTPException(status_code=404, detail="Tracker not found")
    history = db.query(PriceHistory).filter(PriceHistory.tracker_id == tracker.id).order_by(PriceHistory.checked_at.desc()).all()
    return templates.TemplateResponse("tracker.html", {"request": request, "tracker": tracker, "history": history})

@app.get("/api/trackers", response_model=list[TrackerOut])
def api_list_trackers(db: Session = Depends(get_db)):
    items = db.query(Tracker).order_by(Tracker.created_at.desc()).all()
    return [TrackerOut.model_validate(i) for i in items]
