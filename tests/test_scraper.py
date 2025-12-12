"""Comprehensive unit tests for the scraper module.

Tests all scraping functions with mocked HTTP requests to ensure
no network calls are made during testing.
"""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from app.scraper import (
    extract_title,
    parse_price_from_jsonld,
    parse_price_from_meta,
    smart_find_price,
    _text,
    _candidate_score,
    get_price,
    fetch_html,
    PRICE_REGEX,
)


# =============================================================================
# HTML Fixtures
# =============================================================================

@pytest.fixture
def html_with_jsonld():
    """HTML with JSON-LD structured data containing price."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Product Page</title></head>
    <body>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Test Product",
            "offers": {
                "@type": "Offer",
                "price": "99.99",
                "priceCurrency": "USD"
            }
        }
        </script>
        <div class="product">Test Product</div>
    </body>
    </html>
    """


@pytest.fixture
def html_with_jsonld_array():
    """HTML with JSON-LD array of offers."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Multi Offer Product</title></head>
    <body>
        <script type="application/ld+json">
        {
            "@type": "Product",
            "offers": [
                {"price": "49.99", "priceCurrency": "EUR"},
                {"price": "59.99", "priceCurrency": "USD"}
            ]
        }
        </script>
    </body>
    </html>
    """


@pytest.fixture
def html_with_jsonld_list():
    """HTML with JSON-LD as a list."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>List JSON-LD</title></head>
    <body>
        <script type="application/ld+json">
        [
            {"@type": "WebSite", "name": "Test"},
            {
                "@type": "Product",
                "offers": {"price": "199.00", "priceCurrency": "GBP"}
            }
        ]
        </script>
    </body>
    </html>
    """


@pytest.fixture
def html_with_invalid_jsonld():
    """HTML with invalid JSON-LD."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Invalid JSON</title></head>
    <body>
        <script type="application/ld+json">
        { invalid json here
        </script>
    </body>
    </html>
    """


@pytest.fixture
def html_with_meta_price():
    """HTML with price in meta tags."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Meta Price Product</title>
        <meta property="product:price:amount" content="149.99">
        <meta property="product:price:currency" content="USD">
    </head>
    <body>
        <div>Product content</div>
    </body>
    </html>
    """


@pytest.fixture
def html_with_itemprop_meta():
    """HTML with itemprop meta tag."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Itemprop Product</title>
        <meta itemprop="price" content="$79.99">
    </head>
    <body></body>
    </html>
    """


@pytest.fixture
def html_with_twitter_meta():
    """HTML with Twitter meta tag for price."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter Card Product</title>
        <meta name="twitter:data1" content="$29.99">
    </head>
    <body></body>
    </html>
    """


@pytest.fixture
def html_with_price_class():
    """HTML with price in element class."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Class Price</title></head>
    <body>
        <div class="product-price">$59.99</div>
        <div class="was-price strikethrough">$79.99</div>
    </body>
    </html>
    """


@pytest.fixture
def html_with_price_id():
    """HTML with price in element ID."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>ID Price</title></head>
    <body>
        <span id="current-price">$129.00</span>
    </body>
    </html>
    """


@pytest.fixture
def html_with_itemprop_span():
    """HTML with itemprop on span element."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Itemprop Span</title></head>
    <body>
        <span itemprop="price">$199.99</span>
    </body>
    </html>
    """


@pytest.fixture
def html_complex():
    """Complex HTML with multiple price indicators."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Complex Product Page</title></head>
    <body>
        <div class="product-container">
            <h1>Amazing Product</h1>
            <div class="pricing">
                <span class="was-price">Was $199.99</span>
                <span class="current-price final-price">Now $149.99</span>
                <span class="save-amount">Save $50.00!</span>
            </div>
            <button>Add to Cart</button>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def html_no_price():
    """HTML with no price information."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>No Price Page</title></head>
    <body>
        <div>This page has no price information.</div>
    </body>
    </html>
    """


@pytest.fixture
def html_with_selector_price():
    """HTML with price in specific selector."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Selector Test</title></head>
    <body>
        <div id="main-price" class="big-price">$299.99</div>
        <div class="other-price">$399.99</div>
    </body>
    </html>
    """


# =============================================================================
# Test extract_title()
# =============================================================================

class TestExtractTitle:
    """Tests for extract_title() function."""
    
    def test_extract_simple_title(self, html_with_jsonld):
        """Test extracting a simple title."""
        soup = BeautifulSoup(html_with_jsonld, "lxml")
        title = extract_title(soup)
        assert title == "Product Page"
    
    def test_extract_title_strips_whitespace(self):
        """Test that title whitespace is stripped."""
        html = "<html><head><title>  Spaced Title  </title></head></html>"
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        assert title == "Spaced Title"
    
    def test_extract_title_truncates_long(self):
        """Test that long titles are truncated to 200 chars."""
        long_title = "A" * 300
        html = f"<html><head><title>{long_title}</title></head></html>"
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        assert len(title) == 200
        assert title == "A" * 200
    
    def test_extract_title_returns_none_if_missing(self):
        """Test None is returned when title is missing."""
        html = "<html><head></head><body></body></html>"
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        assert title is None
    
    def test_extract_title_empty_title(self):
        """Test empty title tag returns None."""
        html = "<html><head><title></title></head></html>"
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        assert title is None


# =============================================================================
# Test parse_price_from_jsonld()
# =============================================================================

class TestParseJsonLD:
    """Tests for parse_price_from_jsonld() function."""
    
    def test_parse_valid_jsonld(self, html_with_jsonld):
        """Test parsing valid JSON-LD with price."""
        soup = BeautifulSoup(html_with_jsonld, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is not None
        price, currency = result
        assert price == 99.99
        assert currency == "USD"
    
    def test_parse_jsonld_array_offers(self, html_with_jsonld_array):
        """Test parsing JSON-LD with array of offers."""
        soup = BeautifulSoup(html_with_jsonld_array, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is not None
        price, currency = result
        assert price == 49.99  # First offer
        assert currency == "EUR"
    
    def test_parse_jsonld_list(self, html_with_jsonld_list):
        """Test parsing JSON-LD as a list."""
        soup = BeautifulSoup(html_with_jsonld_list, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is not None
        price, currency = result
        assert price == 199.00
        assert currency == "GBP"
    
    def test_parse_invalid_jsonld(self, html_with_invalid_jsonld):
        """Test parsing invalid JSON-LD returns None."""
        soup = BeautifulSoup(html_with_invalid_jsonld, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is None
    
    def test_parse_jsonld_no_offers(self):
        """Test JSON-LD without offers returns None."""
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "name": "Test"}
        </script>
        """
        soup = BeautifulSoup(html, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is None
    
    def test_parse_jsonld_no_price(self):
        """Test JSON-LD with offers but no price returns None."""
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "offers": {"availability": "InStock"}}
        </script>
        """
        soup = BeautifulSoup(html, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is None
    
    def test_parse_jsonld_with_comma_price(self):
        """Test JSON-LD with comma in price."""
        html = """
        <script type="application/ld+json">
        {"@type": "Product", "offers": {"price": "1,299.99", "priceCurrency": "USD"}}
        </script>
        """
        soup = BeautifulSoup(html, "lxml")
        result = parse_price_from_jsonld(soup)
        assert result is not None
        price, _ = result
        assert price == 1299.99


# =============================================================================
# Test parse_price_from_meta()
# =============================================================================

class TestParseMeta:
    """Tests for parse_price_from_meta() function."""
    
    def test_parse_product_price_meta(self, html_with_meta_price):
        """Test parsing product:price:amount meta tag."""
        soup = BeautifulSoup(html_with_meta_price, "lxml")
        result = parse_price_from_meta(soup)
        assert result is not None
        price, currency = result
        assert price == 149.99
        assert currency == "USD"
    
    def test_parse_itemprop_meta(self, html_with_itemprop_meta):
        """Test parsing itemprop price meta tag."""
        soup = BeautifulSoup(html_with_itemprop_meta, "lxml")
        result = parse_price_from_meta(soup)
        assert result is not None
        price, currency = result
        assert price == 79.99
        assert currency == "USD"
    
    def test_parse_twitter_meta(self, html_with_twitter_meta):
        """Test parsing Twitter data1 meta tag."""
        soup = BeautifulSoup(html_with_twitter_meta, "lxml")
        result = parse_price_from_meta(soup)
        assert result is not None
        price, currency = result
        assert price == 29.99
        assert currency == "USD"
    
    def test_parse_meta_no_price(self, html_no_price):
        """Test parsing HTML without price meta tags."""
        soup = BeautifulSoup(html_no_price, "lxml")
        result = parse_price_from_meta(soup)
        assert result is None
    
    def test_parse_meta_empty_content(self):
        """Test meta tag with empty content."""
        html = '<meta property="product:price:amount" content="">'
        soup = BeautifulSoup(html, "lxml")
        result = parse_price_from_meta(soup)
        assert result is None


# =============================================================================
# Test smart_find_price()
# =============================================================================

class TestSmartFindPrice:
    """Tests for smart_find_price() function."""
    
    def test_find_price_by_class(self, html_with_price_class):
        """Test finding price by CSS class."""
        soup = BeautifulSoup(html_with_price_class, "lxml")
        result = smart_find_price(soup)
        assert result is not None
        price, _ = result
        # Should find current price, not was-price
        assert price == 59.99
    
    def test_find_price_by_id(self, html_with_price_id):
        """Test finding price by element ID."""
        soup = BeautifulSoup(html_with_price_id, "lxml")
        result = smart_find_price(soup)
        assert result is not None
        price, _ = result
        assert price == 129.00
    
    def test_find_price_by_itemprop(self, html_with_itemprop_span):
        """Test finding price by itemprop attribute."""
        soup = BeautifulSoup(html_with_itemprop_span, "lxml")
        result = smart_find_price(soup)
        assert result is not None
        price, _ = result
        assert price == 199.99
    
    def test_find_best_price_in_complex_html(self, html_complex):
        """Test finding correct price in complex HTML with multiple prices."""
        soup = BeautifulSoup(html_complex, "lxml")
        result = smart_find_price(soup)
        assert result is not None
        price, _ = result
        # Should prefer current/final price over was-price
        assert price == 149.99
    
    def test_find_no_price(self, html_no_price):
        """Test returns None when no price found."""
        soup = BeautifulSoup(html_no_price, "lxml")
        result = smart_find_price(soup)
        assert result is None


# =============================================================================
# Test _candidate_score()
# =============================================================================

class TestCandidateScore:
    """Tests for _candidate_score() function."""
    
    def test_score_price_in_class(self):
        """Test higher score for element with 'price' in class."""
        html = '<span class="product-price">$99</span>'
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        score = _candidate_score(el, 99.0, "$99")
        assert score >= 3  # 'price' in class gives +3
    
    def test_score_final_price(self):
        """Test higher score for 'final' in class."""
        html = '<span class="final-price">$99</span>'
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        score = _candidate_score(el, 99.0, "$99")
        assert score >= 4  # 'price' + 'final' bonus
    
    def test_score_negative_for_was_price(self):
        """Test negative score for 'was' in text."""
        html = '<span class="old-price">Was $99</span>'
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        score = _candidate_score(el, 99.0, "Was $99")
        assert score < 3  # Should be reduced due to 'was'
    
    def test_score_negative_for_zero_price(self):
        """Test negative score for zero price."""
        html = '<span class="price">$0</span>'
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        score = _candidate_score(el, 0.0, "$0")
        assert score < 0  # Zero price gets -5
    
    def test_score_negative_price(self):
        """Test negative score for negative price value."""
        html = '<span class="price">-$10</span>'
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        score = _candidate_score(el, -10.0, "-$10")
        assert score < 0


# =============================================================================
# Test _text()
# =============================================================================

class TestTextExtraction:
    """Tests for _text() helper function."""
    
    def test_extract_simple_text(self):
        """Test extracting simple text."""
        html = "<span>Hello World</span>"
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        text = _text(el)
        assert text == "Hello World"
    
    def test_extract_normalizes_whitespace(self):
        """Test that whitespace is normalized."""
        html = "<span>Hello    World\n\t  Test</span>"
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("span")
        text = _text(el)
        assert text == "Hello World Test"
    
    def test_extract_nested_text(self):
        """Test extracting text from nested elements."""
        html = "<div><span>Hello</span> <b>World</b></div>"
        soup = BeautifulSoup(html, "lxml")
        el = soup.find("div")
        text = _text(el)
        assert "Hello" in text
        assert "World" in text


# =============================================================================
# Test get_price() with mocked requests
# =============================================================================

class TestGetPrice:
    """Tests for get_price() function with mocked HTTP requests."""
    
    @patch("app.scraper.fetch_html")
    def test_get_price_with_jsonld(self, mock_fetch, html_with_jsonld):
        """Test get_price extracts from JSON-LD."""
        mock_fetch.return_value = html_with_jsonld
        
        price, currency, title = get_price("https://example.com/product")
        
        assert price == 99.99
        assert currency == "USD"
        assert title == "Product Page"
        mock_fetch.assert_called_once_with("https://example.com/product")
    
    @patch("app.scraper.fetch_html")
    def test_get_price_with_meta(self, mock_fetch, html_with_meta_price):
        """Test get_price extracts from meta tags."""
        mock_fetch.return_value = html_with_meta_price
        
        price, currency, title = get_price("https://example.com/product")
        
        assert price == 149.99
        assert currency == "USD"
        mock_fetch.assert_called_once()
    
    @patch("app.scraper.fetch_html")
    def test_get_price_with_selector(self, mock_fetch, html_with_selector_price):
        """Test get_price uses custom selector."""
        mock_fetch.return_value = html_with_selector_price
        
        price, currency, title = get_price(
            "https://example.com/product",
            selector="#main-price"
        )
        
        assert price == 299.99
        assert currency == "USD"
    
    @patch("app.scraper.fetch_html")
    def test_get_price_smart_fallback(self, mock_fetch, html_with_price_class):
        """Test get_price falls back to smart find."""
        mock_fetch.return_value = html_with_price_class
        
        price, currency, title = get_price("https://example.com/product")
        
        assert price == 59.99
        assert currency == "USD"
    
    @patch("app.scraper.fetch_html")
    def test_get_price_no_price_found(self, mock_fetch, html_no_price):
        """Test get_price returns None when no price found."""
        mock_fetch.return_value = html_no_price
        
        price, currency, title = get_price("https://example.com/product")
        
        assert price is None
        assert currency == "USD"  # Default currency
        assert title == "No Price Page"
    
    @patch("app.scraper.fetch_html")
    def test_get_price_priority_order(self, mock_fetch):
        """Test that selector takes priority over JSON-LD."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Priority Test</title></head>
        <body>
            <script type="application/ld+json">
            {"@type": "Product", "offers": {"price": "50.00"}}
            </script>
            <span id="custom">$100.00</span>
        </body>
        </html>
        """
        mock_fetch.return_value = html
        
        # With selector, should get selector price
        price, _, _ = get_price("https://example.com", selector="#custom")
        assert price == 100.00


# =============================================================================
# Test fetch_html() with mocked requests
# =============================================================================

class TestFetchHtml:
    """Tests for fetch_html() with mocked requests."""
    
    @patch("app.scraper.requests.get")
    def test_fetch_html_success(self, mock_get):
        """Test successful HTML fetch."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = fetch_html("https://example.com")
        
        assert result == "<html><body>Test</body></html>"
        mock_get.assert_called_once()
    
    @patch("app.scraper.requests.get")
    def test_fetch_html_uses_headers(self, mock_get):
        """Test that fetch uses correct headers."""
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        fetch_html("https://example.com")
        
        call_args = mock_get.call_args
        assert "headers" in call_args.kwargs
        assert "User-Agent" in call_args.kwargs["headers"]
    
    @patch("app.scraper.requests.get")
    def test_fetch_html_uses_timeout(self, mock_get):
        """Test that fetch uses timeout from settings."""
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        fetch_html("https://example.com")
        
        call_args = mock_get.call_args
        assert "timeout" in call_args.kwargs
        assert call_args.kwargs["timeout"] > 0
    
    @patch("app.scraper.requests.get")
    def test_fetch_html_raises_on_error(self, mock_get):
        """Test that HTTP errors are propagated."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        with pytest.raises(requests.RequestException):
            fetch_html("https://example.com")

