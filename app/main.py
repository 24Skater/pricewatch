import os
import time
import uuid
import hashlib
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from .context import set_request_id, get_request_id

from .database import Base, engine, get_db, SessionLocal
from .models import Tracker, PriceHistory, NotificationProfile
from .schemas import TrackerCreate, TrackerOut, ProfileCreate
from .scheduler import start_scheduler
from .services.tracker_service import TrackerService
from .services.profile_service import ProfileService
from .services.scheduler_service import SchedulerService
from .exceptions import (
    PricewatchException, ValidationError, SecurityError, 
    ScrapingError, DatabaseError, RateLimitError
)
from .logging_config import get_logger, setup_logging
from .config import settings
from .security import rate_limiter
from .monitoring import health_checker, get_prometheus_metrics, pricewatch_requests_total, pricewatch_request_duration_seconds
from .csrf import get_csrf_token, validate_csrf_token, is_csrf_exempt, CSRF_FORM_FIELD

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

# Request ID Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request.
    
    - Generates UUID for each request
    - Stores in context variable for access throughout request lifecycle
    - Adds X-Request-ID header to response
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        req_id = str(uuid.uuid4())
        
        # Store in shared context (accessible in logging)
        set_request_id(req_id)
        
        # Store in request state for template access
        request.state.request_id = req_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response header
        response.headers["X-Request-ID"] = req_id
        
        return response

app.add_middleware(RequestIDMiddleware)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS filter in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Restrict browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (report-only mode for initial rollout)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy-Report-Only"] = csp
        
        return response

app.add_middleware(SecurityHeadersMiddleware)


# Caching Headers Middleware
class CachingHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add appropriate caching headers to responses.
    
    - Static assets: Cache-Control with long max-age
    - Tracker detail pages: ETag support
    - Sensitive endpoints: no-cache
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        
        # Sensitive endpoints - no caching
        if any(path.startswith(prefix) for prefix in ["/admin", "/health", "/metrics", "/api"]):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        # Static files - long cache
        elif path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # Tracker detail pages - short cache with ETag support
        elif path.startswith("/tracker/") and request.method == "GET":
            # Allow short cache but enable revalidation
            response.headers["Cache-Control"] = "private, max-age=60, must-revalidate"
        # Other pages - short cache
        else:
            response.headers["Cache-Control"] = "private, max-age=300"
        
        return response

app.add_middleware(CachingHeadersMiddleware)


# Prometheus Metrics Middleware
class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint (simplified path)
        endpoint = request.url.path
        # Normalize endpoint (remove IDs for better aggregation)
        if "/tracker/" in endpoint and request.method == "GET":
            endpoint = "/tracker/{id}"
        elif "/admin/profiles/" in endpoint:
            endpoint = "/admin/profiles/{id}"
        
        # Record metrics
        pricewatch_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        pricewatch_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response

app.add_middleware(PrometheusMetricsMiddleware)


# Exception handlers for consistent JSON error responses
from fastapi.responses import JSONResponse

@app.exception_handler(PricewatchException)
async def pricewatch_exception_handler(request: Request, exc: PricewatchException):
    """Handle all Pricewatch custom exceptions with structured JSON response."""
    status_codes = {
        "VALIDATION_ERROR": 400,
        "SECURITY_ERROR": 403,
        "SCRAPING_ERROR": 502,
        "DATABASE_ERROR": 500,
        "RATE_LIMIT_ERROR": 429,
        "NOTIFICATION_ERROR": 500,
        "CONFIGURATION_ERROR": 500,
    }
    status_code = status_codes.get(exc.code, 500)
    
    logger.warning(
        f"{exc.code}: {exc.message}",
        extra={"details": exc.details, "path": str(request.url.path)}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """Handle rate limit exceptions with 429 status."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content=exc.to_dict(),
        headers={"Retry-After": "60"}
    )


# CSRF validation dependency for POST endpoints
async def verify_csrf(
    request: Request,
    csrf_token: str = Form(None, alias="csrf_token")
) -> None:
    """Dependency to verify CSRF token in form submissions."""
    from .csrf import csrf_manager
    
    # Skip CSRF for exempt paths
    if is_csrf_exempt(request.url.path):
        return
    
    # Also check header for AJAX requests
    token = csrf_token or request.headers.get("X-CSRF-Token")
    
    if not csrf_manager.validate_token(token, request):
        logger.warning(
            f"CSRF validation failed for {request.method} {request.url.path} "
            f"from {request.client.host}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed. Please refresh the page and try again."
        )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Add CSRF token function to Jinja2 templates
templates.env.globals["csrf_token"] = get_csrf_token
templates.env.globals["csrf_field_name"] = CSRF_FORM_FIELD

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    """Home page with trackers and profiles."""
    try:
        tracker_service = TrackerService(db)
        profile_service = ProfileService(db)
        
        trackers, _ = tracker_service.get_all_trackers()
        profiles = profile_service.get_all_profiles()
        
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "trackers": trackers, "profiles": profiles}
        )
    except Exception as e:
        logger.error(f"Failed to load index page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/trackers", response_class=HTMLResponse)
async def create_tracker(
    request: Request,
    url: str = Form(...),
    alert_method: str = Form(...),
    contact: str = Form(...),
    selector: str = Form(""),
    name: str = Form(""),
    profile_id: int = Form(0),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
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
        
        # Generate ETag based on tracker and latest price check
        etag_data = f"{tracker_id}-{tracker.created_at.isoformat() if tracker.created_at else ''}"
        if history:
            etag_data += f"-{history[0].checked_at.isoformat()}"
        etag = hashlib.md5(etag_data.encode()).hexdigest()
        
        # Check if client has matching ETag
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match == etag:
            return Response(status_code=304)  # Not Modified
        
        response = templates.TemplateResponse(
            "tracker.html", 
            {"request": request, "tracker": tracker, "history": history}
        )
        response.headers["ETag"] = etag
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tracker {tracker_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/tracker/{tracker_id}/refresh", response_class=HTMLResponse)
async def tracker_refresh(
    request: Request,
    tracker_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
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
async def tracker_set_selector(
    request: Request,
    tracker_id: int,
    selector: str = Form(""),
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
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
async def tracker_update(
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
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
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
async def tracker_delete(
    request: Request,
    tracker_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
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
async def profiles_create(
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
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
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
async def profiles_update(
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
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
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
async def profiles_delete(
    request: Request,
    profile_id: int,
    csrf_token: str = Form(None),
    db: Session = Depends(get_db),
    _csrf: None = Depends(verify_csrf),
):
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
        trackers, _ = tracker_service.get_all_trackers()
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
    """Prometheus metrics endpoint."""
    try:
        if settings.enable_metrics:
            metrics_data = get_prometheus_metrics()
            return Response(
                content=metrics_data,
                media_type=CONTENT_TYPE_LATEST
            )
        else:
            # Fallback to JSON metrics if Prometheus is disabled
            health_data = health_checker.comprehensive_health_check()
            return {
                "application": health_data["checks"]["application"],
                "system": health_data["checks"]["system_resources"],
                "uptime": health_data["checks"]["uptime"]
            }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {"error": str(e)}
