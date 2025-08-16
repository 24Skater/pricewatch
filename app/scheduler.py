import os
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .models import Tracker, PriceHistory
from .scraper import get_price
from .alerts import send_email, send_sms

SCHEDULE_MINUTES = int(os.getenv("SCHEDULE_MINUTES", "30"))

def poll_all_trackers(db: Session):
    trackers = db.query(Tracker).filter(Tracker.is_active == True).all()
    for t in trackers:
        try:
            price, currency, title = get_price(t.url, t.selector)
        except Exception as e:
            print(f"[ERROR] fetching {t.url}: {e}")
            continue
        if price is None:
            print(f"[WARN] No price found for {t.url}")
            continue
        delta = None if t.last_price is None else round(price - t.last_price, 2)
        if t.last_price is None or abs(price - t.last_price) > 1e-6:
            ph = PriceHistory(tracker_id=t.id, price=price, delta=delta)
            db.add(ph)
            t.last_price = price
            if not t.name and title:
                t.name = title[:200]
            db.add(t)
            db.commit()
            if delta is not None and abs(delta) > 1e-6:
                sign = "decreased" if delta < 0 else "increased"
                subject = f"Price {sign}: {t.name or t.url}"
                body = (
                    f"The price has {sign} by ${abs(delta):.2f}\n"
                    f"Current price: ${price:.2f}\n"
                    f"URL: {t.url}\n"
                )
                if t.alert_method == "email":
                    send_email(t.contact, subject, body, profile=t.profile)
                else:
                    send_sms(t.contact, subject + "\n" + body, profile=t.profile)

def start_scheduler(db_factory):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(lambda: _job(db_factory), "interval", minutes=SCHEDULE_MINUTES, id="pricewatch")
    scheduler.start()

def _job(db_factory):
    db = db_factory()
    try:
        poll_all_trackers(db)
    finally:
        db.close()
