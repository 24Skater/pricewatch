import re, json
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PricewatchBot/1.0; +https://example.com/bot)"
}

PRICE_REGEX = re.compile(r"""
    (?<![A-Za-z0-9])              # left boundary
    (\$|USD\s*)?                  # optional currency
    ([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?|[0-9]+(?:\.[0-9]{2}))  # number with , and .
    (?![A-Za-z0-9])               # right boundary
""", re.VERBOSE)

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

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

def parse_price_from_selector(soup: BeautifulSoup, selector: Optional[str]) -> Optional[Tuple[float, str]]:
    if not selector:
        return None
    try:
        sel = soup.select_one(selector)
        if sel:
            text = sel.get_text(" ", strip=True)
            m = PRICE_REGEX.search(text)
            if m:
                val = float(m.group(2).replace(",", ""))
                return val, "USD"
    except Exception:
        pass
    return None

def parse_price_anywhere(soup: BeautifulSoup) -> Optional[Tuple[float, str]]:
    candidates = []
    for t in soup.find_all(text=True):
        if "$" in t:
            candidates.append(t)
    texts = candidates + soup.find_all(text=True)
    for t in texts:
        text = str(t)
        m = PRICE_REGEX.search(text)
        if m:
            try:
                return float(m.group(2).replace(",", "")), "USD"
            except Exception:
                continue
    return None

def extract_title(soup: BeautifulSoup) -> Optional[str]:
    if soup.title and soup.title.string:
        return soup.title.string.strip()[:200]
    return None

def get_price(url: str, selector: Optional[str] = None) -> Tuple[Optional[float], str, Optional[str]]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup)

    for fn in (lambda s: parse_price_from_selector(s, selector),
               parse_price_from_jsonld,
               parse_price_from_meta,
               parse_price_anywhere):
        res = fn(soup)
        if res:
            return res[0], res[1], title
    return None, "USD", title
