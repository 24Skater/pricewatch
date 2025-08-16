# Pricewatch — Website Price Tracker (FastAPI)

Track prices from product pages, get alerts (email/SMS) on change, and view a simple trending table.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill credentials
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docker:
```bash
docker compose up --build
```

**Note**: Respect site ToS and robots.txt.
