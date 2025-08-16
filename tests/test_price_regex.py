from app.scraper import PRICE_REGEX

def test_matches():
    for s in ["$1,299.99","USD 19.95","1299.00","$899"]:
        assert PRICE_REGEX.search(s)
