from app.scraper import PRICE_REGEX

def test_price_regex_basic():
    for s in ["$1,299.99", "USD 19.95", "1299.00", "$899"]:
        assert PRICE_REGEX.search(s)

def test_price_regex_boundaries():
    assert PRICE_REGEX.search("Buy now for $99!") is not None
    assert PRICE_REGEX.search("Was $109.99 now $99.99") is not None
