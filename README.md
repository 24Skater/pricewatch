# Pricewatch — per-user SMTP/SMS + editable trackers

This app tracks product prices, sends alerts, and supports **per-user Notification Profiles** for SMTP/Twilio. 
It includes a **smart auto-detect** scraper (no selector needed), optional **JS fallback**, and full **edit/delete** for trackers.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# open http://localhost:8000
```

### Optional JS fallback (for heavy JS pages)
```bash
pip install playwright
python -m playwright install chromium
# then set USE_JS_FALLBACK=1 in .env and restart
```

### Admin
- Create profiles at **/admin/profiles**
- Add trackers at **/** and choose a profile (or use default env)
- Edit trackers at **/tracker/{id}/edit**
- Use **Poll now** or **Save & Poll** to refresh immediately

> Dev note: credentials are stored in SQLite for demo simplicity. Use a secrets manager + encryption for production.
