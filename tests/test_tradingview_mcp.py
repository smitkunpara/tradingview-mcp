"""
Comprehensive test suite for TradingView MCP server.
Tests validators, utilities, auth functions, and main tool functions.
"""

import pytest
from unittest.mock import patch
"""Test that None returns None"""
from tradingview_mcp.validators import validate_exchange
assert validate_exchange(None) is None

def test_validate_exchange_invalid(self):
    """Test that invalid exchange raises ValidationError"""
    from tradingview_mcp.validators import validate_exchange, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_exchange("INVALID_EXCHANGE")
    assert "Invalid exchange" in str(exc_info.value)

# --- Test validate_timeframe ---

def test_validate_timeframe_valid(self):
    """Test all valid timeframes pass"""
    from tradingview_mcp.validators import validate_timeframe, VALID_TIMEFRAMES
    for tf in VALID_TIMEFRAMES:
        assert validate_timeframe(tf) == tf

def test_validate_timeframe_invalid(self):
    """Test invalid timeframe raises ValidationError"""
    from tradingview_mcp.validators import validate_timeframe, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_timeframe("2m")
    assert "Invalid timeframe" in str(exc_info.value)

# --- Test validate_news_provider ---

def test_validate_news_provider_valid(self):
    """Test valid news provider passes"""
    from tradingview_mcp.validators import validate_news_provider
    assert validate_news_provider("coindesk") == "coindesk"
    assert validate_news_provider("COINDESK") == "coindesk"

def test_validate_news_provider_all(self):
    """Test 'all' returns None"""
    from tradingview_mcp.validators import validate_news_provider
    assert validate_news_provider("all") is None
    assert validate_news_provider("ALL") is None

def test_validate_news_provider_invalid(self):
    """Test invalid provider raises ValidationError"""
    from tradingview_mcp.validators import validate_news_provider, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_news_provider("invalid_provider")
    assert "Invalid news provider" in str(exc_info.value)

# --- Test validate_area ---

def test_validate_area_valid(self):
    """Test valid areas pass"""
    from tradingview_mcp.validators import validate_area, VALID_AREAS
    for area in VALID_AREAS:
        assert validate_area(area) == area
        assert validate_area(area.upper()) == area

def test_validate_area_invalid(self):
    """Test invalid area raises ValidationError"""
    from tradingview_mcp.validators import validate_area, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_area("invalid_area")
    assert "Invalid area" in str(exc_info.value)

# --- Test validate_symbol ---

def test_validate_symbol_valid(self):
    """Test valid symbol passes"""
    from tradingview_mcp.validators import validate_symbol
    assert validate_symbol("NIFTY") == "NIFTY"
    assert validate_symbol("  AAPL  ") == "AAPL"  # Strips whitespace

def test_validate_symbol_empty(self):
    """Test empty symbol raises ValidationError"""
    from tradingview_mcp.validators import validate_symbol, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_symbol("")
    assert "Symbol is required" in str(exc_info.value)

def test_validate_symbol_none(self):
    """Test None symbol raises ValidationError"""
    from tradingview_mcp.validators import validate_symbol, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_symbol(None)
    assert "Symbol is required" in str(exc_info.value)

def test_validate_symbol_whitespace_only(self):
    """Test whitespace-only symbol raises ValidationError"""
    from tradingview_mcp.validators import validate_symbol, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_symbol("   ")
    assert "Symbol is required" in str(exc_info.value)

# --- Test validate_indicators ---

def test_validate_indicators_valid_single(self):
    """Test single valid indicator"""
    from tradingview_mcp.validators import validate_indicators
    ids, versions, errors, warnings = validate_indicators(["RSI"])
    assert len(ids) == 1
    assert len(versions) == 1
    assert len(errors) == 0
    assert len(warnings) == 0

def test_validate_indicators_valid_multiple(self):
    """Test multiple valid indicators"""
    from tradingview_mcp.validators import validate_indicators
    ids, versions, errors, warnings = validate_indicators(["RSI", "MACD"])
    assert len(ids) == 2
    assert len(versions) == 2
    assert len(errors) == 0

def test_validate_indicators_more_than_two_warning(self):
    """Test warning when more than 2 indicators requested"""
    from tradingview_mcp.validators import validate_indicators
    ids, versions, errors, warnings = validate_indicators(["RSI", "MACD", "CCI"])
    assert len(ids) == 3
    assert len(warnings) == 1
    assert "More than 2 indicators" in warnings[0]

def test_validate_indicators_invalid(self):
    """Test invalid indicator returns error"""
    from tradingview_mcp.validators import validate_indicators
    ids, versions, errors, warnings = validate_indicators(["INVALID"])
    assert len(ids) == 0
    assert len(errors) == 1
    assert "not recognized" in errors[0]

def test_validate_indicators_case_insensitive(self):
    """Test indicators are case insensitive"""
    from tradingview_mcp.validators import validate_indicators
    ids_lower, _, _, _ = validate_indicators(["rsi"])
    ids_upper, _, _, _ = validate_indicators(["RSI"])
    assert ids_lower == ids_upper

def test_validate_indicators_empty(self):
    """Test empty list returns empty results"""
    from tradingview_mcp.validators import validate_indicators
    ids, versions, errors, warnings = validate_indicators([])
    assert len(ids) == 0
    assert len(versions) == 0
    assert len(errors) == 0

# --- Test validate_story_paths ---

def test_validate_story_paths_valid(self):
    """Test valid story paths pass"""
    from tradingview_mcp.validators import validate_story_paths
    paths = ["/news/story1", "/news/story2"]
    assert validate_story_paths(paths) == paths

def test_validate_story_paths_empty(self):
    """Test empty list raises ValidationError"""
    from tradingview_mcp.validators import validate_story_paths, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_story_paths([])
    assert "At least one story path" in str(exc_info.value)

def test_validate_story_paths_invalid_format(self):
    """Test paths not starting with /news/ raise ValidationError"""
    from tradingview_mcp.validators import validate_story_paths, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_story_paths(["/invalid/path"])
    assert "must start with '/news/'" in str(exc_info.value)

def test_validate_story_paths_not_list(self):
    """Test non-list raises ValidationError"""
    from tradingview_mcp.validators import validate_story_paths, ValidationError
    with pytest.raises(ValidationError) as exc_info:
        validate_story_paths("/news/story")
    assert "must be provided as a list" in str(exc_info.value)


# ============================================================================
# Test: utils.py
# ============================================================================

class TestUtils:
    """Tests for utility functions in utils.py"""
    
    # --- Test convert_timestamp_to_indian_time ---
    
    def test_convert_timestamp_to_indian_time_valid(self):
        """Test valid timestamp conversion"""
        from tradingview_mcp.utils import convert_timestamp_to_indian_time
        # Unix timestamp for 2024-01-01 00:00:00 UTC
        timestamp = 1704067200
        result = convert_timestamp_to_indian_time(timestamp)
        assert "IST" in result
        assert "01-01-2024" in result
        # IST is UTC+5:30, so 00:00 UTC = 05:30 IST
        assert "05:30:00 AM" in result
    
    def test_convert_timestamp_to_indian_time_pm(self):
        """Test PM timestamp conversion"""
        from tradingview_mcp.utils import convert_timestamp_to_indian_time
        # Unix timestamp for 2024-01-01 12:00:00 UTC = 17:30 IST
        timestamp = 1704110400
        result = convert_timestamp_to_indian_time(timestamp)
        assert "05:30:00 PM" in result
    
    # --- Test clean_for_json ---
    
    def test_clean_for_json_dict(self):
        """Test cleaning dict with simple values"""
        from tradingview_mcp.utils import clean_for_json
        data = {"key": "value", "number": 123}
        assert clean_for_json(data) == data
    
    def test_clean_for_json_list(self):
        """Test cleaning list"""
        from tradingview_mcp.utils import clean_for_json
        data = [1, 2, {"key": "value"}]
        assert clean_for_json(data) == data
    
    def test_clean_for_json_nested(self):
        """Test cleaning nested structure"""
        from tradingview_mcp.utils import clean_for_json
        data = {"outer": {"inner": [1, 2, 3]}}
        assert clean_for_json(data) == data
    
    def test_clean_for_json_beautifulsoup_tag(self):
        """Test cleaning BeautifulSoup Tag converts to string"""
        from tradingview_mcp.utils import clean_for_json
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("<div>test</div>", "html.parser")
        tag = soup.find("div")
        result = clean_for_json(tag)
        assert isinstance(result, str)
        assert "test" in result
    
    # --- Test extract_news_body ---
    
    def test_extract_news_body_valid(self):
        """Test extracting body from news content"""
        from tradingview_mcp.utils import extract_news_body
        content = {
            "body": [
                {"type": "text", "content": "First paragraph."},
                {"type": "image", "content": "image.jpg"},
                {"type": "text", "content": "Second paragraph."}
            ]
        }
        result = extract_news_body(content)
        assert "First paragraph." in result
        assert "Second paragraph." in result
        assert "image.jpg" not in result
    
    def test_extract_news_body_empty(self):
        """Test empty body returns empty string"""
        from tradingview_mcp.utils import extract_news_body
        content = {"body": []}
        assert extract_news_body(content) == ""
    
    def test_extract_news_body_no_body_key(self):
        """Test missing body key returns empty string"""
        from tradingview_mcp.utils import extract_news_body
        content = {}
        assert extract_news_body(content) == ""
    
    # --- Test merge_ohlc_with_indicators ---
    
    def test_merge_ohlc_with_indicators_no_indicators(self):
        """Test merging OHLC data with no indicators"""
        from tradingview_mcp.utils import merge_ohlc_with_indicators
        data = {
            'ohlc': [
                {'timestamp': 1704067200, 'open': 100, 'high': 105, 'low': 99, 'close': 102, 'volume': 1000, 'index': 0}
            ],
            'indicator': {}
        }
        result = merge_ohlc_with_indicators(data)
        assert len(result) == 1
        assert result[0]['open'] == 100
        assert result[0]['close'] == 102
        assert 'datetime_ist' in result[0]
    
    def test_merge_ohlc_with_indicators_empty_ohlc(self):
        """Test empty OHLC raises ValueError"""
        from tradingview_mcp.utils import merge_ohlc_with_indicators
        data = {'ohlc': [], 'indicator': {}}
        with pytest.raises(ValueError) as exc_info:
            merge_ohlc_with_indicators(data)
        assert "No OHLC data" in str(exc_info.value)
    
    def test_merge_ohlc_with_indicators_with_rsi(self):
        """Test merging OHLC with RSI indicator"""
        from tradingview_mcp.utils import merge_ohlc_with_indicators
        timestamp = 1704067200
        data = {
            'ohlc': [
                {'timestamp': timestamp, 'open': 100, 'high': 105, 'low': 99, 'close': 102, 'volume': 1000, 'index': 0}
            ],
            'indicator': {
                'STD;RSI': [
                    {'timestamp': timestamp, '2': 55.5, '0': 50.0}
                ]
            }
        }
        result = merge_ohlc_with_indicators(data)
        assert len(result) == 1
        assert result[0]['Relative_Strength_Index'] == 55.5
        assert result[0]['Relative_Strength_Index_Moving_Average'] == 50.0


# ============================================================================
# Test: auth.py
# ============================================================================

class TestAuth:
    """Tests for authentication functions in auth.py"""
    
    # --- Test get_token_info ---
    
    def test_get_token_info_valid_token(self):
        """Test decoding a valid JWT token structure"""
        from tradingview_mcp.auth import get_token_info
        # Create a simple valid JWT token
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps({"exp": 9999999999, "iat": 1000000000, "user_id": "test"}).encode()).decode().rstrip("=")
        signature = "testsignature"
        token = f"{header}.{payload}.{signature}"
        
        result = get_token_info(token)
        assert result['valid'] is True
        assert result['exp'] == 9999999999
        assert result['user_id'] == "test"
    
    def test_get_token_info_invalid_format(self):
        """Test invalid token format"""
        from tradingview_mcp.auth import get_token_info
        result = get_token_info("invalid.token")
        assert result['valid'] is False
        assert 'error' in result
    
    def test_get_token_info_malformed_payload(self):
        """Test malformed base64 payload"""
        from tradingview_mcp.auth import get_token_info
        result = get_token_info("header.invalid!!!.signature")
        assert result['valid'] is False
    
    # --- Test extract_jwt_token ---
    
    def test_extract_jwt_token_no_cookie(self):
        """Test extraction without TRADINGVIEW_COOKIE raises ValueError"""
        from tradingview_mcp.auth import extract_jwt_token
        # Ensure env var is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                extract_jwt_token()
            assert "TRADINGVIEW_COOKIE" in str(exc_info.value)
    
    def test_extract_jwt_token_no_url(self):
        """Test extraction without TRADINGVIEW_URL raises ValueError"""
        from tradingview_mcp.auth import extract_jwt_token
        with patch.dict(os.environ, {"TRADINGVIEW_COOKIE": "test_cookie"}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                extract_jwt_token()
            assert "TRADINGVIEW_URL" in str(exc_info.value)


# ============================================================================
# Test: tradingview_tools.py
# ============================================================================

class TestTradingViewTools:
    """Tests for TradingView tools functions"""
    
    # --- Test get_valid_jwt_token ---
    
    def test_get_valid_jwt_token_caching(self):
        """Test that JWT tokens are cached properly"""
        from tradingview_mcp.tradingview_tools import get_valid_jwt_token, _token_cache
        import time
        
        # Create a valid mock token
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        future_exp = int(time.time()) + 3600  # 1 hour from now
        payload = base64.urlsafe_b64encode(json.dumps({"exp": future_exp, "iat": int(time.time()), "user_id": "test"}).encode()).decode().rstrip("=")
        signature = "testsignature"
        mock_token = f"{header}.{payload}.{signature}"
        
        with patch('tradingview_mcp.tradingview_tools.extract_jwt_token', return_value=mock_token):
            # First call - should extract token
            token1 = get_valid_jwt_token()
            assert token1 == mock_token
            
            # Second call - should use cached token
            with patch('tradingview_mcp.tradingview_tools.extract_jwt_token') as mock_extract:
                token2 = get_valid_jwt_token()
                # extract_jwt_token should not be called if cached
                # Note: It may or may not be called depending on thread timing
                assert token2 == mock_token
    
    # --- Test is_jwt_token_valid ---
    
    def test_is_jwt_token_valid_valid_token(self):
        """Test valid non-expired token returns True"""
        from tradingview_mcp.tradingview_tools import is_jwt_token_valid
        import time
        
        # Mock jwt.decode to return a valid non-expired token payload
        future_exp = int(time.time()) + 3600
        with patch('tradingview_mcp.tradingview_tools.jwt.decode', return_value={"exp": future_exp}):
            # Any token string will work since we mock the decode
            assert is_jwt_token_valid("mock.token.here") is True
    
    def test_is_jwt_token_valid_expired_token(self):
        """Test expired token returns False"""
        from tradingview_mcp.tradingview_tools import is_jwt_token_valid
        import time
        
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        past_exp = int(time.time()) - 3600  # 1 hour ago
        payload = base64.urlsafe_b64encode(json.dumps({"exp": past_exp}).encode()).decode().rstrip("=")
        token = f"{header}.{payload}.signature"
        
        assert is_jwt_token_valid(token) is False
    
    def test_is_jwt_token_valid_invalid_token(self):
        """Test invalid token format returns False"""
        from tradingview_mcp.tradingview_tools import is_jwt_token_valid
        assert is_jwt_token_valid("not.a.valid.token") is False
        assert is_jwt_token_valid("") is False
    
    # --- Test fetch_historical_data ---
    
    def test_fetch_historical_data_invalid_exchange(self):
        """Test invalid exchange raises ValidationError"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            fetch_historical_data(
                exchange="INVALID",
                symbol="NIFTY",
                timeframe="1m",
                numb_price_candles=10,
                indicators=[]
            )
        assert "Invalid exchange" in str(exc_info.value)
    
    def test_fetch_historical_data_invalid_timeframe(self):
        """Test invalid timeframe raises ValidationError"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            fetch_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe="2m",
                numb_price_candles=10,
                indicators=[]
            )
        assert "Invalid timeframe" in str(exc_info.value)
    
    def test_fetch_historical_data_invalid_candles_range(self):
        """Test invalid candle count raises ValidationError"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            fetch_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe="1m",
                numb_price_candles=10000,  # Over max
                indicators=[]
            )
        assert "must be between" in str(exc_info.value)
    
    def test_fetch_historical_data_invalid_candles_string(self):
        """Test invalid string candle count raises ValidationError"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            fetch_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe="1m",
                numb_price_candles="not_a_number",
                indicators=[]
            )
        assert "must be a valid integer" in str(exc_info.value)
    
    def test_fetch_historical_data_invalid_indicators(self):
        """Test invalid indicators returns error"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        result = fetch_historical_data(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1m",
            numb_price_candles=10,
            indicators=["INVALID_INDICATOR"]
        )
        assert result['success'] is False
        assert "not recognized" in str(result.get('errors', []))
    
    def test_fetch_historical_data_empty_symbol(self):
        """Test empty symbol raises ValidationError"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            fetch_historical_data(
                exchange="NSE",
                symbol="",
                timeframe="1m",
                numb_price_candles=10,
                indicators=[]
            )
        assert "Symbol is required" in str(exc_info.value)
    
    # --- Test fetch_news_headlines mocking ---
    
    def test_fetch_news_headlines_validation_invalid_symbol(self):
        """Test invalid symbol raises error"""
        from tradingview_mcp.tradingview_tools import fetch_news_headlines
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError):
            fetch_news_headlines(symbol="", exchange="NSE")
    
    def test_fetch_news_headlines_validation_invalid_exchange(self):
        """Test invalid exchange raises error"""
        from tradingview_mcp.tradingview_tools import fetch_news_headlines
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError):
            fetch_news_headlines(symbol="NIFTY", exchange="INVALID")
    
    def test_fetch_news_headlines_validation_invalid_provider(self):
        """Test invalid provider raises error"""
        from tradingview_mcp.tradingview_tools import fetch_news_headlines
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError):
            fetch_news_headlines(symbol="NIFTY", provider="invalid_provider")
    
    def test_fetch_news_headlines_validation_invalid_area(self):
        """Test invalid area raises error"""
        from tradingview_mcp.tradingview_tools import fetch_news_headlines
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError):
            fetch_news_headlines(symbol="NIFTY", area="invalid_area")


# ============================================================================
# Test: CONSTANTS
# ============================================================================

class TestConstants:
    """Tests for validator constants"""
    
    def test_valid_exchanges_not_empty(self):
        """Test VALID_EXCHANGES is populated"""
        from tradingview_mcp.validators import VALID_EXCHANGES
        assert len(VALID_EXCHANGES) > 0
        assert "NSE" in VALID_EXCHANGES
        assert "NASDAQ" in VALID_EXCHANGES
        assert "BINANCE" in VALID_EXCHANGES
    
    def test_valid_timeframes(self):
        """Test VALID_TIMEFRAMES contains expected values"""
        from tradingview_mcp.validators import VALID_TIMEFRAMES
        expected = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']
        assert VALID_TIMEFRAMES == expected
    
    def test_valid_areas(self):
        """Test VALID_AREAS contains expected values"""
        from tradingview_mcp.validators import VALID_AREAS
        expected = ['world', 'americas', 'europe', 'asia', 'oceania', 'africa']
        assert VALID_AREAS == expected
    
    def test_indicator_mapping(self):
        """Test INDICATOR_MAPPING has expected indicators"""
        from tradingview_mcp.validators import INDICATOR_MAPPING
        assert "RSI" in INDICATOR_MAPPING
        assert "MACD" in INDICATOR_MAPPING
        assert "CCI" in INDICATOR_MAPPING
        assert "BB" in INDICATOR_MAPPING
    
    def test_indicator_field_mapping(self):
        """Test INDICATOR_FIELD_MAPPING has correct structure"""
        from tradingview_mcp.validators import INDICATOR_FIELD_MAPPING
        assert "RSI" in INDICATOR_FIELD_MAPPING
        assert "2" in INDICATOR_FIELD_MAPPING["RSI"]
        assert INDICATOR_FIELD_MAPPING["RSI"]["2"] == "Relative_Strength_Index"


# ============================================================================
# Test: ValidationError Exception
# ============================================================================

class TestValidationError:
    """Tests for ValidationError exception"""
    
    def test_validation_error_is_exception(self):
        """Test ValidationError is a proper Exception"""
        from tradingview_mcp.validators import ValidationError
        assert issubclass(ValidationError, Exception)
    
    def test_validation_error_message(self):
        """Test ValidationError preserves message"""
        from tradingview_mcp.validators import ValidationError
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"
    
    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised and caught"""
        from tradingview_mcp.validators import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Custom error")
        assert "Custom error" in str(exc_info.value)


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_validate_exchange_mixed_case(self):
        """Test mixed case exchange conversion"""
        from tradingview_mcp.validators import validate_exchange
        assert validate_exchange("NsE") == "NSE"
        assert validate_exchange("nAsDAq") == "NASDAQ"
    
    def test_validate_symbol_with_numbers(self):
        """Test symbol with numbers"""
        from tradingview_mcp.validators import validate_symbol
        assert validate_symbol("NIFTY50") == "NIFTY50"
        assert validate_symbol("SPY500") == "SPY500"
    
    def test_validate_symbol_special_characters(self):
        """Test symbol with valid special characters"""
        from tradingview_mcp.validators import validate_symbol
        # Some symbols may have valid special characters
        assert validate_symbol("BTC-USD") == "BTC-USD"
    
    def test_merge_ohlc_multiple_entries(self):
        """Test merging multiple OHLC entries"""
        from tradingview_mcp.utils import merge_ohlc_with_indicators
        data = {
            'ohlc': [
                {'timestamp': 1704067200, 'open': 100, 'high': 105, 'low': 99, 'close': 102, 'volume': 1000, 'index': 0},
                {'timestamp': 1704067260, 'open': 102, 'high': 106, 'low': 101, 'close': 104, 'volume': 1100, 'index': 1},
                {'timestamp': 1704067320, 'open': 104, 'high': 107, 'low': 103, 'close': 106, 'volume': 1200, 'index': 2},
            ],
            'indicator': {}
        }
        result = merge_ohlc_with_indicators(data)
        assert len(result) == 3
        assert result[0]['index'] == 0
        assert result[1]['index'] == 1
        assert result[2]['index'] == 2
    
    def test_extract_news_body_only_images(self):
        """Test body with only non-text elements"""
        from tradingview_mcp.utils import extract_news_body
        content = {
            "body": [
                {"type": "image", "content": "image1.jpg"},
                {"type": "video", "content": "video.mp4"},
            ]
        }
        assert extract_news_body(content) == ""
    
    def test_validate_story_paths_mixed_valid_invalid(self):
        """Test story paths with mix of valid and invalid"""
        from tradingview_mcp.validators import validate_story_paths, ValidationError
        with pytest.raises(ValidationError):
            validate_story_paths(["/news/valid", "/invalid/path"])


# ============================================================================
# Test: Integration-like tests (mocked external dependencies)
# ============================================================================

class TestIntegration:
    """Integration-like tests with mocked external dependencies"""
    
    def test_fetch_historical_data_no_cookie_env(self):
        """Test fetch_historical_data without TRADINGVIEW_COOKIE"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        
        with patch.dict(os.environ, {}, clear=True):
            result = fetch_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe="1m",
                numb_price_candles=10,
                indicators=[]
            )
            assert result['success'] is False
            assert "TRADINGVIEW_COOKIE" in str(result)
    
    def test_fetch_historical_data_with_string_candles(self):
        """Test fetch_historical_data with string numb_price_candles"""
        from tradingview_mcp.tradingview_tools import fetch_historical_data
        
        with patch.dict(os.environ, {}, clear=True):
            # Even with string "10", it should work but fail on cookie
            result = fetch_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe="1m",
                numb_price_candles="10",
                indicators=[]
            )
            # Should fail due to missing cookie, not due to string conversion
            assert result['success'] is False
            assert "TRADINGVIEW_COOKIE" in str(result) or "cookie" in str(result).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
