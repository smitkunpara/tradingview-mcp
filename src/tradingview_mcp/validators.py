"""
Centralized validators for TradingView MCP server.
Contains all validation constants and functions used across the application.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

# === EXCHANGE VALIDATORS ===
VALID_EXCHANGES = [
    "BINANCE", "BINANCEUS", "BITCOKE", "BITFINEX", "BITSTAMP", "BITTREX", "BYBIT", 
    "CAPITALCOM", "CEXIO", "CURRENCYCOM", "EASYMARKETS", "EIGHTCAP", "EXMO", 
    "FOREXCOM", "FTX", "FXCM", "GEMINI", "GLOBALPRIME", "INDEX", "KRAKEN", "OANDA", 
    "OKCOIN", "PEPPERSTONE", "SAXO", "SKILLING", "TIMEX", "TRADESTATION", "VANTAGE", 
    "KUCOIN", "ADX", "ALOR", "AMEX", "ASX", "ATHEX", "BAHRAIN", "BASESWAP", "BCBA", 
    "BCS", "BELEX", "BER", "BET", "BINGX", "BIST", "BISWAP", "BITAZZA", "BITBNS", 
    "BITFLYER", "BITGET", "BITHUMB", "BITKUB", "BITMART", "BITMEX", "BITPANDAPRO", 
    "BITRUE", "BITVAVO", "BIVA", "BLACKBULL", "BLOFIN", "BME", "BMFBOVESPA", "BMV", 
    "BSE", "BSSE", "BTSE", "BVB", "BVC", "BVCV", "BVL", "BVMT", "BX", "CAMELOT", 
    "CAMELOT3ARBITRUM", "CBOE", "CBOT", "CBOT_MINI", "CFFEX", "CITYINDEX", "CME", 
    "CME_MINI", "COINBASE", "COINEX", "COMEX", "COMEX_MINI", "CRYPTO", "CRYPTOCOM", 
    "CRYPTOCAP", "CSE", "CSECY", "CSELK", "CSEMA", "CURVE", "DELTA", "DERIBIT", 
    "DFM", "DJ", "DSEBD", "DUS", "DYDX", "ECONOMICS", "EGX", "EUREX", "EURONEXT", 
    "EUROTLX", "FINRA", "FSE", "FTSEMYX", "FWB", "FX", "FX_IDC", "FXOPEN", "GATEIO", 
    "GETTEX", "GPW", "HAM", "HAN", "HITBTC", "HKEX", "HNX", "HONEYSWAP", 
    "HONEYSWAPPOLYGON", "HOSE", "HSI", "HTX", "HUOBI", "ICEAD", "ICEEUR", "ICESG", 
    "ICEUS", "IDX", "JSE", "KATANA", "KRX", "KSE", "LS", "LSE", "LSIN", "LSX", 
    "LUXSE", "MATBAROFEX", "MCX", "MERCADO", "MEXC", "MGEX", "MIL", "MMFINANCE", 
    "MOEX", "MUN", "MYX", "NAG", "NASDAQ", "NASDAQDUBAI", "NCDEX", "NEO", 
    "NEWCONNECT", "NGM", "NSE", "NSEKE", "NSENG", "NYMEX", "NYMEX_MINI", "NYSE", 
    "NZX", "OKCOIN", "OKX", "OMXCOP", "OMXHEX", "OMXICE", "OMXRSE", "OMXSTO", 
    "OMXTSE", "OMXVSE", "ORCA", "OSE", "OSL", "OTC", "PANCAKESWAP", 
    "PANCAKESWAP3BSC", "PANCAKESWAP3ETH", "PANGOLIN", "PHEMEX", "PHILLIPNOVA", 
    "PIONEX", "POLONIEX", "PSE", "PSECZ", "PSX", "PULSEX", "QSE", "QUICKSWAP", 
    "QUICKSWAP3POLYGONZKEVM", "QUICKSWAP3POLYGON", "RAYDIUM", "RUS", "SAPSE", 
    "SET", "SGX", "SHFE", "SIX", "SP", "SPARKS", "SPOOKYSWAP", "SSE", "SUSHISWAP", 
    "SUSHISWAPPOLYGON", "SWB", "SZSE", "TADAWUL", "TAIFEX", "TASE", "TFEX", "TFX", 
    "THRUSTER3", "TOCOM", "TOKENIZE", "TPEX", "TRADEGATE", "TRADERJOE", "TSE", 
    "TSX", "TSXV", "TVC", "TWSE", "UNISWAP", "UNISWAP3ARBITRUM", "UNISWAP3AVALANCHE", 
    "UNISWAP3BASE", "UNISWAP3BSC", "UNISWAP3ETH", "UNISWAP3OPTIMISM", 
    "UNISWAP3POLYGON", "UPBIT", "UPCOM", "VELODROME", "VERSEETH", "VIE", 
    "VVSFINANCE", "WAGYUSWAP", "WHITEBIT", "WOONETWORK", "XETR", "XEXCHANGE", "ZOOMEX"
]

# === TIMEFRAME VALIDATORS ===
VALID_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M']

# === NEWS PROVIDER VALIDATORS ===
VALID_NEWS_PROVIDERS = [
    "the_block", "cointelegraph", "beincrypto", "newsbtc", "dow-jones", 
    "cryptonews", "coindesk", "cryptoglobe", "tradingview", "zycrypto", 
    "todayq", "cryptopotato", "u_today", "cryptobriefing", "coindar", 
    "bitcoin_com", "all"
]

# === AREA VALIDATORS ===
VALID_AREAS = ['world', 'americas', 'europe', 'asia', 'oceania', 'africa']

# === INDICATOR MAPPING ===
INDICATOR_MAPPING = {
    "RSI": ("STD;RSI", "44.0"),
    "MACD": ("STD;MACD", "38.0"),
    "CCI": ("STD;CCI", "37.0"),
    "BB": ("STD;Bollinger_Bands", "32.0"),
}

# === INDICATOR FIELD MAPPING ===
# Maps each indicator to its output fields with their respective indices
INDICATOR_FIELD_MAPPING = {
    "RSI": {
        "2": "Relative_Strength_Index",
        "0": "Relative_Strength_Index_Moving_Average"
    },
    "MACD": {
        "4": "Moving_Average_Convergence_Divergence_macd",
        "5": "Moving_Average_Convergence_Divergence_signal", 
        "2": "Moving_Average_Convergence_Divergence_histogram"
    },
    "CCI": {
        "0": "Commodity_Channel_Index",
        "1": "Commodity_Channel_Index_Moving_Average"
    },
    "BB": {
        "0": "Bollinger_Bands_middle_line",
        "1": "Bollinger_Bands_top_line", 
        "2": "Bollinger_Bands_bottom_line"
    }
}

VALID_INDICATORS = list(INDICATOR_MAPPING.keys())


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_exchange(exchange: Optional[str]) -> Optional[str]:
    """
    Validate exchange name and convert to uppercase.
    
    Args:
        exchange: Exchange name to validate
        
    Returns:
        Uppercase exchange name or None
        
    Raises:
        ValidationError: If exchange is invalid
    """
    if exchange is None:
        return None
    
    exchange_upper = exchange.upper()
    if exchange_upper not in VALID_EXCHANGES:
        raise ValidationError(
            f"Invalid exchange '{exchange}'. Must be one of: {', '.join(VALID_EXCHANGES[:10])}... "
            f"(and {len(VALID_EXCHANGES) - 10} more)"
        )
    return exchange_upper


def validate_timeframe(timeframe: str) -> str:
    """
    Validate timeframe string.
    
    Args:
        timeframe: Timeframe to validate
        
    Returns:
        Valid timeframe string
        
    Raises:
        ValidationError: If timeframe is invalid
    """
    if timeframe not in VALID_TIMEFRAMES:
        raise ValidationError(
            f"Invalid timeframe '{timeframe}'. Must be one of: {', '.join(VALID_TIMEFRAMES)}"
        )
    return timeframe


def validate_news_provider(provider: str) -> Optional[str]:
    """
    Validate news provider.
    
    Args:
        provider: News provider to validate
        
    Returns:
        Valid provider string or None for 'all'
        
    Raises:
        ValidationError: If provider is invalid
    """
    provider_lower = provider.lower()
    if provider_lower not in VALID_NEWS_PROVIDERS:
        raise ValidationError(
            f"Invalid news provider '{provider}'. Must be one of: {', '.join(VALID_NEWS_PROVIDERS)}"
        )
    
    # Return None if 'all' to fetch from all providers
    return None if provider_lower == "all" else provider_lower


def validate_area(area: str) -> str:
    """
    Validate geographical area.
    
    Args:
        area: Area to validate
        
    Returns:
        Valid area string
        
    Raises:
        ValidationError: If area is invalid
    """
    area_lower = area.lower()
    if area_lower not in VALID_AREAS:
        raise ValidationError(
            f"Invalid area '{area}'. Must be one of: {', '.join(VALID_AREAS)}"
        )
    return area_lower


def validate_indicators(indicators: List[str]) -> tuple[List[str], List[str], List[str], List[str]]:
    """
    Validate and map indicators to TradingView IDs.
    
    Note: Free TradingView accounts are limited to maximum 2 indicators per request.
    
    Args:
        indicators: List of indicator names
        
    Returns:
        Tuple of (indicator_ids, indicator_versions, errors)
    """
    indicator_ids = []
    indicator_versions = []
    errors = []
    warnings = []
    
    # Note: free TradingView accounts support only 2 indicators per single
    # request. The caller (fetch_historical_data) will automatically batch
    # requests when more than 2 indicators are requested. We therefore do
    # not fail here; instead include a warning in errors so callers/logs
    # can surface the behaviour to users if desired.
    MAX_INDICATORS_PER_REQUEST = 2
    if len(indicators) > MAX_INDICATORS_PER_REQUEST:
        warnings.append(
            f"More than {MAX_INDICATORS_PER_REQUEST} indicators requested ({len(indicators)}). "
            "The library will fetch indicators in batches of 2 per request to work "
            "around free account limits."
        )
    
    for indicator in indicators:
        indicator_upper = indicator.upper()
        if indicator_upper in INDICATOR_MAPPING:
            ind_id, ind_version = INDICATOR_MAPPING[indicator_upper]
            indicator_ids.append(ind_id)
            indicator_versions.append(ind_version)
        else:
            errors.append(
                f"Indicator '{indicator}' not recognized. Valid indicators: {', '.join(VALID_INDICATORS)}"
            )
    
    return indicator_ids, indicator_versions, errors, warnings


def validate_symbol(symbol: Optional[str]) -> str:
    """
    Validate symbol is provided.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Valid symbol string
        
    Raises:
        ValidationError: If symbol is None or empty
    """
    if not symbol or not symbol.strip():
        raise ValidationError(
            "Symbol is required. Please provide a valid trading symbol (e.g., 'AAPL', 'NIFTY', 'BTCUSD')"
        )
    return symbol.strip()


def validate_story_paths(story_paths: List[str]) -> List[str]:
    """
    Validate story paths list.
    
    Args:
        story_paths: List of story paths
        
    Returns:
        Valid story paths list
        
    Raises:
        ValidationError: If story_paths is empty or invalid
    """
    if not story_paths:
        raise ValidationError("At least one story path is required")
    
    if not isinstance(story_paths, list):
        raise ValidationError("Story paths must be provided as a list")
    
    # Validate each path starts with /news/
    invalid_paths = [p for p in story_paths if not p.startswith('/news/')]
    if invalid_paths:
        raise ValidationError(
            f"Invalid story paths format. All paths must start with '/news/'. "
            f"Invalid: {invalid_paths[:3]}..."
        )
    
    return story_paths