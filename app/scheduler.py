import os
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .services.scheduler_service import SchedulerService
from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

def start_scheduler(db_factory):
    """Start the background scheduler."""
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        lambda: _job(db_factory), 
        "interval", 
        minutes=settings.schedule_minutes, 
        id="pricewatch"
    )
    scheduler.start()
    logger.info(f"Started scheduler with {settings.schedule_minutes} minute intervals")

def _job(db_factory):
    """Background job to poll all trackers."""
    db = db_factory()
    try:
        scheduler_service = SchedulerService(db)
        scheduler_service.poll_all_trackers()
    except Exception as e:
        logger.error(f"Scheduler job failed: {e}")
    finally:
        db.close()
