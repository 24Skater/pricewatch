import os
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from .database import Base, engine, get_db, SessionLocal
from .models import Tracker, PriceHistory, NotificationProfile
from .schemas import TrackerCreate, TrackerOut, ProfileCreate
from .scheduler import start_scheduler
from .services.tracker_service import TrackerService
from .services.profile_service import ProfileService
from .services.scheduler_service import SchedulerService
from .exceptions import ValidationError, SecurityError, ScrapingError, DatabaseError
from .logging_config import get_logger, setup_logging
from .config import settings
from .security import rate_limiter
from .monitoring import health_checker

# Setup logging
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Pricewatch application")
    Base.metadata.create_all(bind=engine)
    start_scheduler(SessionLocal)
    yield
    # Shutdown
    logger.info("Shutting down Pricewatch application")

app = FastAPI(
    title="Pricewatch",
    description="A price tracking application with notifications",
    version="2.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    """Home page with trackers and profiles."""
    try:
        tracker_service = TrackerService(db)
        profile_service = ProfileService(db)
        
        trackers = tracker_service.get_all_trackers()
        profiles = profile_service.get_all_profiles()
        
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "trackers": trackers, "profiles": profiles}
        )
    except Exception as e:
        logger.error(f"Failed to load index page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    """Create a new tracker."""
    try:
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.is_allowed(client_ip, settings.rate_limit_per_minute):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Create tracker data
        tracker_data = TrackerCreate(
            url=url,
            alert_method=alert_method,
            contact=contact,
            selector=selector or None,
            name=name or None,
            profile_id=profile_id or None,
        )
        
        # Use service layer
        tracker_service = TrackerService(db)
        tracker = tracker_service.create_tracker(tracker_data)
        
        logger.info(f"Created tracker {tracker.id} for {tracker.url}")
        return RedirectResponse(url=f"/tracker/{tracker.id}", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValidationError as e:
        logger.warning(f"Validation error creating tracker: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        logger.warning(f"Security error creating tracker: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create tracker: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tracker/{tracker_id}", response_class=HTMLResponse)
def tracker_detail(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    """Get tracker details with price history."""
    try:
        tracker_service = TrackerService(db)
        tracker = tracker_service.get_tracker(tracker_id)
        
        if not tracker:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        history = db.query(PriceHistory).filter(
            PriceHistory.tracker_id == tracker_id
        ).order_by(PriceHistory.checked_at.desc()).all()
        
        return templates.TemplateResponse(
            "tracker.html", 
            {"request": request, "tracker": tracker, "history": history}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tracker/{tracker_id}/refresh", response_class=HTMLResponse)
def tracker_refresh(tracker_id: int, db: Session = Depends(get_db)):
    """Refresh tracker price."""
    try:
        tracker_service = TrackerService(db)
        tracker = tracker_service.get_tracker(tracker_id)
        
        if not tracker:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        price, currency = tracker_service.refresh_tracker_price(tracker_id)
        
        logger.info(f"Refreshed tracker {tracker_id}: ${price}")
        return RedirectResponse(url=f"/tracker/{tracker_id}?ok=1", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValidationError as e:
        logger.warning(f"Validation error refreshing tracker {tracker_id}: {e}")
        return RedirectResponse(
            url=f"/tracker/{tracker_id}?error={quote_plus(str(e))}", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except ScrapingError as e:
        logger.warning(f"Scraping error refreshing tracker {tracker_id}: {e}")
        return RedirectResponse(
            url=f"/tracker/{tracker_id}?error={quote_plus(str(e))}", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Failed to refresh tracker {tracker_id}: {e}")
        return RedirectResponse(
            url=f"/tracker/{tracker_id}?error={quote_plus('Internal server error')}", 
            status_code=status.HTTP_303_SEE_OTHER
        )


@app.post("/tracker/{tracker_id}/selector", response_class=HTMLResponse)
def tracker_set_selector(tracker_id: int, selector: str = Form(""), db: Session = Depends(get_db)):
    """Update tracker selector."""
    try:
        tracker_service = TrackerService(db)
        tracker = tracker_service.get_tracker(tracker_id)
        
        if not tracker:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        tracker.selector = selector or None
        db.add(tracker)
        db.commit()
        
        logger.info(f"Updated selector for tracker {tracker_id}")
        return RedirectResponse(url=f"/tracker/{tracker_id}/refresh", status_code=status.HTTP_303_SEE_OTHER)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update selector for tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tracker/{tracker_id}/edit", response_class=HTMLResponse)
def tracker_edit(tracker_id: int, request: Request, db: Session = Depends(get_db)):
    """Edit tracker form."""
    try:
        tracker_service = TrackerService(db)
        profile_service = ProfileService(db)
        
        tracker = tracker_service.get_tracker(tracker_id)
        if not tracker:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        profiles = profile_service.get_all_profiles()
        
        return templates.TemplateResponse(
            "tracker_edit.html", 
            {"request": request, "tracker": tracker, "profiles": profiles}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load edit form for tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    """Update tracker."""
    try:
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.is_allowed(client_ip, settings.rate_limit_per_minute):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Create tracker data
        tracker_data = TrackerCreate(
            url=url,
            alert_method=alert_method,
            contact=contact,
            selector=selector or None,
            name=name or None,
            profile_id=profile_id or None,
        )
        
        # Use service layer
        tracker_service = TrackerService(db)
        tracker = tracker_service.update_tracker(tracker_id, tracker_data)
        
        if not tracker:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        # Update active status
        tracker.is_active = bool(is_active)
        db.add(tracker)
        db.commit()
        
        # Poll now if requested
        if poll_now:
            try:
                price, currency = tracker_service.refresh_tracker_price(tracker_id)
                logger.info(f"Polled tracker {tracker_id} after update: ${price}")
            except Exception as e:
                logger.warning(f"Poll-after-save failed for tracker {tracker_id}: {e}")
        
        logger.info(f"Updated tracker {tracker_id}")
        return RedirectResponse(url=f"/tracker/{tracker_id}", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValidationError as e:
        logger.warning(f"Validation error updating tracker {tracker_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except SecurityError as e:
        logger.warning(f"Security error updating tracker {tracker_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tracker/{tracker_id}/delete", response_class=HTMLResponse)
def tracker_delete(tracker_id: int, db: Session = Depends(get_db)):
    """Delete tracker."""
    try:
        tracker_service = TrackerService(db)
        success = tracker_service.delete_tracker(tracker_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tracker not found")
        
        logger.info(f"Deleted tracker {tracker_id}")
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/profiles", response_class=HTMLResponse)
def profiles_list(request: Request, db: Session = Depends(get_db)):
    """List all notification profiles."""
    try:
        profile_service = ProfileService(db)
        profiles = profile_service.get_all_profiles()
        
        return templates.TemplateResponse(
            "admin/profiles.html", 
            {"request": request, "profiles": profiles}
        )
    except Exception as e:
        logger.error(f"Failed to load profiles: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/profiles/new", response_class=HTMLResponse)
def profiles_new(request: Request):
    """New profile form."""
    return templates.TemplateResponse(
        "admin/profile_form.html", 
        {"request": request, "profile": None}
    )

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
    """Create new notification profile."""
    try:
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.is_allowed(client_ip, settings.rate_limit_per_minute):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Create profile data
        profile_data = ProfileCreate(
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
        
        # Use service layer
        profile_service = ProfileService(db)
        profile = profile_service.create_profile(profile_data)
        
        logger.info(f"Created profile {profile.id}: {profile.name}")
        return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValidationError as e:
        logger.warning(f"Validation error creating profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/profiles/{profile_id}/edit", response_class=HTMLResponse)
def profiles_edit(profile_id: int, request: Request, db: Session = Depends(get_db)):
    """Edit profile form."""
    try:
        profile_service = ProfileService(db)
        profile = profile_service.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return templates.TemplateResponse(
            "admin/profile_form.html", 
            {"request": request, "profile": profile}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load edit form for profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    """Update notification profile."""
    try:
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.is_allowed(client_ip, settings.rate_limit_per_minute):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Create profile data
        profile_data = ProfileCreate(
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
        
        # Use service layer
        profile_service = ProfileService(db)
        profile = profile_service.update_profile(profile_id, profile_data)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        logger.info(f"Updated profile {profile_id}")
        return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)
        
    except ValidationError as e:
        logger.warning(f"Validation error updating profile {profile_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/profiles/{profile_id}/delete", response_class=HTMLResponse)
def profiles_delete(profile_id: int, db: Session = Depends(get_db)):
    """Delete notification profile."""
    try:
        profile_service = ProfileService(db)
        success = profile_service.delete_profile(profile_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        logger.info(f"Deleted profile {profile_id}")
        return RedirectResponse(url="/admin/profiles", status_code=status.HTTP_303_SEE_OTHER)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trackers", response_model=list[TrackerOut])
def api_list_trackers(db: Session = Depends(get_db)):
    """API endpoint to list all trackers."""
    try:
        tracker_service = TrackerService(db)
        trackers = tracker_service.get_all_trackers()
        return [TrackerOut.model_validate(tracker) for tracker in trackers]
    except Exception as e:
        logger.error(f"Failed to list trackers via API: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment
    }

@app.get("/health/detailed")
def detailed_health():
    """Detailed health check endpoint."""
    try:
        health_data = health_checker.comprehensive_health_check()
        return health_data
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/metrics")
def metrics():
    """Application metrics endpoint."""
    try:
        health_data = health_checker.comprehensive_health_check()
        return {
            "application": health_data["checks"]["application"],
            "system": health_data["checks"]["system_resources"],
            "uptime": health_data["checks"]["uptime"]
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {"error": str(e)}
