# Pricewatch (Profiles) — per-user SMTP/SMS

This fork adds **Notification Profiles** so each person can save their own SMTP (email) and Twilio (SMS) credentials in an **Admin** section, then select a profile when creating a tracker.

> ⚠️ Dev note: This stores secrets in **SQLite** for demo purposes. For production, use a secrets manager and encrypted storage.

## Quickstart
```bash
python -m venv .venv && . .venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# open http://localhost:8000
```
- Create profiles at **/admin/profiles**
- Add trackers on the home page and choose a profile
- Scheduler runs every `SCHEDULE_MINUTES`

## Important
- If you used a previous version, **delete `pricewatch.db`** to allow the new tables/columns to be created (or add proper migrations with Alembic).
