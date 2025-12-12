"""Web scraping module for extracting prices from product pages.

This module provides functions to fetch HTML content and extract prices
using multiple strategies: JSON-LD structured data, meta tags, and 
smart content analysis.
"""

import re
import json
from typing import Optional, Tuple, List, Set
import requests
from bs4 import BeautifulSoup, Tag
from contextlib import suppress

from app.config import settings

# Type alias for price result: (price, currency, title)
PriceResult = Tuple[Optional[float], str, Optional[str]]

# Type alias for internal price parsing: (price, currency)
PriceParseResult = Tuple[float, str]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PricewatchBot/1.0; +https://example.com/bot)"
}

PRICE_REGEX = re.compile(r"""
    (?<![A-Za-z0-9])
    (\$|USD\s*)?
    ([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2}))
    (?![A-Za-z0-9])
""", re.VERBOSE)

# CSS selectors that commonly contain prices
HINT_SELECTORS: List[str] = [
    "[itemprop=price]",
    "meta[itemprop=price]",
    "*[class*=price i]",
    "*[id*=price i]",
    "[data-test*=price i]",
    "[data-qa*=price i]",
]

# Words that indicate a non-current price (sale, discount, etc.)
NEG_WORDS: Set[str] = {
    "save", "saving", "was", "strike", "strikethrough", 
    "coupon", "per month", "msrp", "list", "discount"
}

# Words that indicate the actual current price
POS_NEAR: Set[str] = {
    "final", "current", "your price", "our price", "add to cart", "buy"
}


def fetch_html(url: str) -> str:
    """Fetch HTML content from a URL using standard HTTP request.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The HTML content as a string
        
    Raises:
        requests.RequestException: If the request fails
    """
    resp = requests.get(url, headers=HEADERS, timeout=settings.request_timeout)
    resp.raise_for_status()
    return resp.text


def fetch_html_js(url: str) -> str:
    """Fetch HTML content from a URL using headless browser (Playwright).
    
    This is used as a fallback when standard HTTP requests don't return
    JavaScript-rendered content.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The rendered HTML content as a string
        
    Raises:
        Exception: If browser automation fails
    """
    from playwright.sync_api import sync_playwright
    # Convert seconds to milliseconds for Playwright
    timeout_ms = settings.request_timeout * 1000
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        with suppress(Exception):
            page.wait_for_timeout(1500)
        html = page.content()
        browser.close()
    return html


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract the page title from HTML.
    
    Args:
        soup: Parsed BeautifulSoup object
        
    Returns:
        The page title truncated to 200 characters, or None if not found
    """
    if soup.title and soup.title.string:
        return soup.title.string.strip()[:200]
    return None


def parse_price_from_jsonld(soup: BeautifulSoup) -> Optional[PriceParseResult]:
    """Extract price from JSON-LD structured data.
    
    Looks for Schema.org Product/Offer structured data in script tags.
    
    Args:
        soup: Parsed BeautifulSoup object
        
    Returns:
        Tuple of (price, currency) if found, None otherwise
    """
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


def parse_price_from_meta(soup: BeautifulSoup) -> Optional[PriceParseResult]:
    """Extract price from HTML meta tags.
    
    Checks common meta tag patterns used by e-commerce sites.
    
    Args:
        soup: Parsed BeautifulSoup object
        
    Returns:
        Tuple of (price, currency) if found, None otherwise
    """
    metas: List[Tuple[str, dict]] = [
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


def _text(el: Tag) -> str:
    """Extract clean text content from an element.
    
    Args:
        el: BeautifulSoup Tag element
        
    Returns:
        Cleaned text with whitespace normalized
    """
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


def _nearby_text(el: Tag, limit_nodes: int = 3) -> str:
    """Extract text from parent elements for context analysis.
    
    Args:
        el: BeautifulSoup Tag element to start from
        limit_nodes: Maximum number of parent levels to traverse
        
    Returns:
        Combined lowercase text from parent elements (max 1000 chars)
    """
    out: List[str] = []
    cur: Optional[Tag] = el
    for _ in range(limit_nodes):
        if not cur or not getattr(cur, "parent", None):
            break
        cur = cur.parent
        with suppress(Exception):
            out.append(cur.get_text(" ", strip=True).lower())
    return " ".join(out)[:1000]


def _candidate_score(el: Tag, price_val: float, raw_text: str) -> int:
    """Calculate a confidence score for a price candidate.
    
    Higher scores indicate more likely to be the actual current price.
    
    Args:
        el: BeautifulSoup Tag containing the price
        price_val: The parsed price value
        raw_text: The raw text content of the element
        
    Returns:
        Integer score (higher = more confident this is the correct price)
    """
    score = 0
    id_class = " ".join(filter(None, [
        (el.get("id") or ""), 
        " ".join(el.get("class") or [])
    ])).lower()
    
    if "price" in id_class:
        score += 3
    if any(w in id_class for w in ("final", "current", "sale")):
        score += 1
    
    low = raw_text.lower()
    if any(w in low for w in NEG_WORDS):
        score -= 3
    
    near = _nearby_text(el)
    if any(w in near for w in POS_NEAR):
        score += 2
    
    if price_val <= 0.0:
        score -= 5
    
    return score


def smart_find_price(soup: BeautifulSoup) -> Optional[PriceParseResult]:
    """Find price using heuristic analysis of page content.
    
    Uses CSS selectors and text analysis to find price elements,
    then scores candidates to find the most likely current price.
    
    Args:
        soup: Parsed BeautifulSoup object
        
    Returns:
        Tuple of (price, currency) if found, None otherwise
    """
    nodes: List[Tag] = []
    
    # Collect candidate elements from known selectors
    for sel in HINT_SELECTORS:
        with suppress(Exception):
            nodes += list(soup.select(sel))
    
    # Also check elements containing price indicators
    with suppress(Exception):
        for el in soup.find_all(text=True):
            t = str(el)
            if "$" in t or "USD" in t:
                if el.parent:
                    nodes.append(el.parent)
    
    best: Optional[Tuple[int, float, Tag]] = None
    seen: Set[int] = set()
    
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


def get_price(url: str, selector: Optional[str] = None) -> PriceResult:
    """Fetch a URL and extract the product price.
    
    Tries multiple strategies in order:
    1. User-provided CSS selector
    2. JSON-LD structured data
    3. Meta tags
    4. Smart content analysis
    5. JavaScript fallback (if enabled)
    
    Args:
        url: The product page URL to scrape
        selector: Optional CSS selector to target specific price element
        
    Returns:
        Tuple of (price, currency, title) where price may be None if not found
    """
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup)
    
    # Try user-provided selector first
    if selector:
        with suppress(Exception):
            sel = soup.select_one(selector)
            if sel:
                m = PRICE_REGEX.search(_text(sel))
                if m:
                    return float(m.group(2).replace(",", "")), "USD", title
    
    # Try structured data and meta tags
    for fn in (parse_price_from_jsonld, parse_price_from_meta):
        r = fn(soup)
        if r:
            return r[0], r[1], title
    
    # Try smart content analysis
    r = smart_find_price(soup)
    if r:
        return r[0], r[1], title
    
    # JavaScript fallback for dynamic content
    if settings.use_js_fallback:
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
