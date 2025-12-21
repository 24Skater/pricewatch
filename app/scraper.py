import os, re, json
from typing import Optional, Tuple, Iterable
import requests
from bs4 import BeautifulSoup
from contextlib import suppress

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}
USE_JS = os.getenv("USE_JS_FALLBACK", "true") in {"1", "true", "True"}

PRICE_REGEX = re.compile(r"""
    (?<![A-Za-z0-9])
    (\$|USD\s*)?
    ([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2}))
    (?![A-Za-z0-9])
""", re.VERBOSE)

def fetch_html(url: str) -> str:
    import time
    import random
    
    # Add a small random delay to avoid being detected as a bot
    time.sleep(random.uniform(1, 3))
    
    # Try with session for better connection handling
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        resp = session.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        # If regular request fails, try with different headers
        fallback_headers = HEADERS.copy()
        fallback_headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        session.headers.update(fallback_headers)
        resp = session.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        return resp.text

def fetch_html_js(url: str) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers=HEADERS
        )
        page = context.new_page()
        
        # Set additional headers to look more like a real browser
        page.set_extra_http_headers({
            'Accept': HEADERS['Accept'],
            'Accept-Language': HEADERS['Accept-Language'],
            'Accept-Encoding': HEADERS['Accept-Encoding'],
        })
        
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait a bit for any dynamic content to load
        with suppress(Exception):
            page.wait_for_timeout(2000)
        
        html = page.content()
        browser.close()
    return html

def extract_title(soup: BeautifulSoup) -> Optional[str]:
    if soup.title and soup.title.string:
        return soup.title.string.strip()[:200]
    return None

def parse_price_from_jsonld(soup: BeautifulSoup) -> Optional[Tuple[float, str]]:
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            offers = item.get("offers")
            if not offers:
                continue
            if isinstance(offers, list):
                offers = offers[0]
            price = offers.get("price")
            currency = offers.get("priceCurrency", "USD")
            try:
                if price is not None:
                    return float(str(price).replace(",", "")), currency
            except Exception:
                pass
    return None

def parse_price_from_meta(soup: BeautifulSoup) -> Optional[Tuple[float, str]]:
    metas = [
        ("meta", {"property": "product:price:amount"}),
        ("meta", {"itemprop": "price"}),
        ("meta", {"name": "twitter:data1"}),
    ]
    for name, attrs in metas:
        tag = soup.find(name, attrs=attrs)
        if tag and tag.get("content"):
            text = tag["content"]
            m = PRICE_REGEX.search(text)
            if m:
                val = float(m.group(2).replace(",", ""))
                return val, "USD"
    return None

HINT_SELECTORS = [
    "[itemprop=price]",
    "meta[itemprop=price]",
    "*[class*=price i]",
    "*[id*=price i]",
    "[data-test*=price i]",
    "[data-qa*=price i]",
    # Sweetwater specific selectors
    ".price-current",
    ".product-price",
    ".price",
    "[class*='price']",
    "[class*='cost']",
    "[class*='amount']",
    # Generic e-commerce selectors
    ".price-value",
    ".current-price",
    ".sale-price",
    ".final-price",
    ".total-price",
    ".amount",
    ".cost",
    ".value",
]
NEG_WORDS = {"save", "saving", "was", "strike", "strikethrough", "coupon", "per month", "msrp", "list", "discount"}
POS_NEAR = {"final", "current", "your price", "our price", "add to cart", "buy"}

def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))

def _nearby_text(el, limit_nodes: int = 3) -> str:
    out = []
    cur = el
    for _ in range(limit_nodes):
        if not cur or not getattr(cur, "parent", None):
            break
        cur = cur.parent
        with suppress(Exception):
            out.append(cur.get_text(" ", strip=True).lower())
    return " ".join(out)[:1000]

def _candidate_score(el, price_val: float, raw_text: str) -> int:
    score = 0
    id_class = " ".join(filter(None, [(el.get("id") or ""), " ".join(el.get("class") or [])])).lower()
    if "price" in id_class: score += 3
    if any(w in id_class for w in ("final", "current", "sale")): score += 1
    low = raw_text.lower()
    if any(w in low for w in NEG_WORDS): score -= 3
    near = _nearby_text(el)
    if any(w in near for w in POS_NEAR): score += 2
    if price_val <= 0.0: score -= 5
    return score

def smart_find_price(soup: BeautifulSoup) -> Optional[Tuple[float, str]]:
    nodes = []
    for sel in HINT_SELECTORS:
        with suppress(Exception):
            nodes += list(soup.select(sel))
    with suppress(Exception):
        for el in soup.find_all(text=True):
            t = str(el)
            if "$" in t or "USD" in t:
                if el.parent:
                    nodes.append(el.parent)
    best = None
    seen = set()
    for el in nodes:
        if not getattr(el, "get_text", None):
            continue
        if id(el) in seen:
            continue
        seen.add(id(el))
        raw = _text(el)
        m = PRICE_REGEX.search(raw)
        if not m:
            continue
        val = float(m.group(2).replace(",", ""))
        s = _candidate_score(el, val, raw)
        if (best is None) or (s > best[0]) or (s == best[0] and val <= best[1]):
            best = (s, val, el)
    if best:
        return best[1], "USD"
    return None

def get_price(url: str, selector: Optional[str] = None) -> Tuple[Optional[float], str, Optional[str]]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup)
    if selector:
        with suppress(Exception):
            sel = soup.select_one(selector)
            if sel:
                m = PRICE_REGEX.search(_text(sel))
                if m:
                    return float(m.group(2).replace(",", "")), "USD", title
    for fn in (parse_price_from_jsonld, parse_price_from_meta):
        r = fn(soup)
        if r:
            return r[0], r[1], title
    r = smart_find_price(soup)
    if r:
        return r[0], r[1], title
    if USE_JS:
        try:
            html_js = fetch_html_js(url)
            soup_js = BeautifulSoup(html_js, "lxml")
            if selector:
                with suppress(Exception):
                    sel = soup_js.select_one(selector)
                    if sel:
                        m = PRICE_REGEX.search(_text(sel))
                        if m:
                            return float(m.group(2).replace(",", "")), "USD", title
            for fn in (parse_price_from_jsonld, parse_price_from_meta):
                r = fn(soup_js)
                if r:
                    return r[0], r[1], title
            r = smart_find_price(soup_js)
            if r:
                return r[0], r[1], title
        except Exception as e:
            print(f"[WARN] JS fallback failed: {e}")
    return None, "USD", title
