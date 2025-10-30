"""
FastMCP server for TradingView data scraping.
Provides tools for fetching historical data, news headlines, and news content.
"""

from typing import Annotated, List, Optional, Literal, Union
from pydantic import Field
from fastmcp import FastMCP
from dotenv import load_dotenv
import json

from .tradingview_tools import (
    fetch_historical_data,
    fetch_news_headlines,
    fetch_news_content,
    fetch_all_indicators,
    fetch_ideas,
    process_option_chain_with_analysis
)
from .validators import (
    VALID_EXCHANGES, VALID_TIMEFRAMES, VALID_NEWS_PROVIDERS,
    VALID_AREAS, ValidationError,INDICATOR_MAPPING,validate_symbol
)


# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("TradingView-MCP")


@mcp.tool
def get_historical_data(
    exchange: Annotated[str, Field(
        description=f"Stock exchange name (e.g., 'NSE', 'NASDAQ', 'BINANCE'). Must be one of the valid exchanges like {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.",
        min_length=2,
        max_length=30
    )],
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.",
        min_length=1,
        max_length=20
    )],
    timeframe: Annotated[Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'], Field(
        description="Time interval for each candle. Options: 1m (1 minute), 5m, 15m, 30m, 1h (1 hour), 2h, 4h, 1d (1 day), 1w (1 week), 1M (1 month)"
    )],
    numb_price_candles: Annotated[int, Field(
        description="Number of historical candles to fetch (1-5000). More candles = longer history. E.g., 100 for last 100 periods.",
        ge=1,
        le=5000
    )],
    indicators: Annotated[List[str], Field(
        description=(
            f"List of technical indicators to include. Options: {', '.join(INDICATOR_MAPPING.keys())}. "
            "Example: ['RSI', 'MACD', 'CCI', 'BB']. Leave empty for no indicators."
        )
    )] = []
) -> dict:
    """
    Fetch historical OHLCV data with technical indicators from TradingView.
    
    Retrieves historical price data (Open, High, Low, Close, Volume) for any
    trading instrument along with specified technical indicators. Data includes
    timestamps converted to Indian Standard Time (IST).
    
    Returns a dictionary containing:
    - success: Boolean indicating if operation succeeded
    - data: List of OHLCV candles with indicator values
    - errors: List of any errors or warnings
    - metadata: Information about the request
    
    Example usage:
    - Get last 100 1-minute candles for NIFTY with RSI:
      get_historical_data("NSE", "NIFTY", "1m", 100, ["RSI"])
    
    Note: Requires active internet connection to fetch data from TradingView.
    """
    try:
        result = fetch_historical_data(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            numb_price_candles=numb_price_candles,
            indicators=indicators
        )
        #export result in the the export/<timstamp>_<symbol>_<timeframe>.json
        try:
            timestamp = result.get("data", {})[0].get("datetime_ist")
        except:
            timestamp = "no-timestamp"
        filename = f"/home/smitkunpara/Desktop/Trading bot/export/{timestamp}_{symbol}_{timeframe}.json"

        with open(filename, 'w') as f:
            json.dump(result, f, indent=4)
        
        return {"file_path":filename , "data" : result}
    
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "data": [],
            "help": "Please check the parameter values and try again."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": [],
            "help": "An unexpected error occurred. Please verify your inputs and try again."
        }


@mcp.tool
def get_news_headlines(
    symbol: Annotated[str, Field(
        description="Trading symbol for news (e.g., 'NIFTY', 'AAPL', 'BTC'). Required. Search online for correct symbol.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[Optional[str], Field(
        description=f"Optional exchange filter. One of: {', '.join(VALID_EXCHANGES[:10])}... Leave empty for all exchanges.",
        min_length=2,
        max_length=30
    )] = None,
    provider: Annotated[str, Field(
        description=f"News provider filter. Options: {', '.join(VALID_NEWS_PROVIDERS[:8])}... or 'all' for all providers.",
        min_length=3,
        max_length=20
    )] = "all",
    area: Annotated[Literal['world', 'americas', 'europe', 'asia', 'oceania', 'africa'], Field(
        description="Geographical area filter for news. Default is 'asia'."
    )] = 'asia'
) -> list:
    """
    Scrape latest news headlines from TradingView for a specific symbol.
    
    Fetches recent news headlines related to a trading symbol from various
    news providers. Returns structured headline data including title, source,
    publication time, and story paths for fetching full content.
    
    Returns a list of headlines, each containing:
    - title: Headline text
    - provider: News source
    - published: Publication timestamp
    - source: Original source URL
    - storyPath: Path for fetching full article content
    
    Example usage:
    - Get all news for NIFTY from NSE: 
      get_news_headlines("NIFTY", "NSE", "all", "asia")
    - Get crypto news for Bitcoin:
      get_news_headlines("BTC", None, "coindesk", "world")
    
    Use the storyPath from results with get_news_content() to fetch full articles.
    """
    try:
        headlines = fetch_news_headlines(
            symbol=symbol,
            exchange=exchange,
            provider=provider,
            area=area
        )
        
        if not headlines:
            return {
                "success": True,
                "message": f"No news found for symbol '{symbol}'",
                "headlines": [],
                "count": 0
            }
        
        return headlines
        
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "headlines": [],
            "help": f"Valid exchanges: {', '.join(VALID_EXCHANGES[:5])}..., "
                   f"Valid providers: {', '.join(VALID_NEWS_PROVIDERS[:5])}..., "
                   f"Valid areas: {', '.join(VALID_AREAS)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to fetch news: {str(e)}",
            "headlines": [],
            "help": "Please verify the symbol exists and try again."
        }


@mcp.tool
def get_news_content(
    story_paths: Annotated[List[str], Field(
        description="List of story paths from news headlines. Each path must start with '/news/'. Get these from get_news_headlines() results.",
        min_length=1,
        max_length=20
    )]
) -> list:
    """
    Fetch full news article content using story paths from headlines.
    
    Retrieves the complete article text for news stories using the story paths
    obtained from get_news_headlines(). Processes multiple articles in a single
    request and extracts the main text content.
    
    Returns a list of articles, each containing:
    - success: Whether content was fetched successfully
    - title: Article title
    - body: Full article text content
    - story_path: Original story path used
    - error: Error message if fetch failed (only on failure)
    
    Example usage:
    1. First get headlines: headlines = get_news_headlines("AAPL")
    2. Extract story paths: paths = [h["storyPath"] for h in headlines[:3]]
    3. Get full content: get_news_content(paths)
    
    Note: Some articles may fail to load due to source restrictions.
    The function will still return partial results for successful fetches.
    """
    try:
        articles = fetch_news_content(story_paths)
        
        successful = [a for a in articles if a.get("success", False)]
        failed = [a for a in articles if not a.get("success", False)]
        
        return articles
        
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "articles": [],
            "help": "Story paths must start with '/news/' and come from get_news_headlines() results"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to fetch news content: {str(e)}",
            "articles": [],
            "help": "Please verify the story paths are valid and try again"
        }


@mcp.tool
def get_all_indicators(
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Required.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[str, Field(
        description=(
            "Stock exchange name (e.g., 'NSE', 'NASDAQ'). Must be one of the valid exchanges. "
            f"Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format."
        ),
        min_length=2,
        max_length=30
    )],
    timeframe: Annotated[Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'], Field(
        description=(
            "Time interval for indicator snapshot. Valid options: "
            f"{', '.join(VALID_TIMEFRAMES)}"
        )
    )] = '1m'
) -> dict:
    """
    Return current values for all available technical indicators for a symbol.

    This tool calls the internal indicators scraper and returns a dictionary of
    current indicator values (a snapshot). It is designed to provide only the
    latest/current values (not historical series).

    Parameters
    - symbol (str): Trading symbol, e.g. 'NIFTY', 'AAPL'.
    - exchange (str): Exchange name, e.g. 'NSE'. Use uppercase from VALID_EXCHANGES.
    - timeframe (str): Timeframe for the indicator snapshot. One of: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M.

    Returns
    - success (bool): Whether the fetch succeeded.
    - data (dict): Mapping of indicator name -> current value (when success=True).
    - message (str): Error message when success=False.

    Example
    - get_all_indicators('NIFTY', 'NSE', '1m')

    Note: The underlying scraper may require a TRADINGVIEW_JWT_TOKEN environment
    variable to be set for private API access. If missing you may receive errors.
    """
    try:
        # Validate parameters explicitly using centralized validators so errors are
        # consistent with the rest of the codebase and reference VALID_* constants.
        from .validators import validate_exchange, validate_timeframe, validate_symbol

        exchange = validate_exchange(exchange)
        symbol = validate_symbol(symbol)
        timeframe = validate_timeframe(timeframe)

        result = fetch_all_indicators(exchange=exchange, symbol=symbol, timeframe=timeframe)
        return result
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "data": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": {}
        }


@mcp.tool
def get_ideas(
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.",
        min_length=1,
        max_length=20
    )],
    startPage: Annotated[int, Field(
        description="Starting page number for scraping ideas",
        ge=1,
        le=10
    )] = 1,
    endPage: Annotated[int, Field(
        description="Ending page number for scraping ideas",
        ge=1,
        le=10
    )] = 1,
    sort: Annotated[Literal['popular', 'recent'], Field(
        description="Sorting order for ideas. 'popular' for most liked, 'recent' for latest."
    )] = 'popular'
) -> dict:
    """
    Scrape trading ideas from TradingView for a specific symbol.

    Fetches trading ideas related to a trading symbol from TradingView. Returns structured idea data including title, author, publication time, and idea content.

    Parameters:
    - symbol (str): Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD').
    - startPage (int): Starting page number for scraping ideas.
    - endPage (int): Ending page number for scraping ideas. Must be >= startPage.
    - sort (str): Sorting order for ideas. Options: 'popular' or 'recent'.

    Returns:
    - success (bool): Whether the scrape was successful.
    - ideas (list): List of scraped ideas with details.
    - count (int): Number of ideas scraped.
    - message (str): Error message if scrape failed.

    Example usage:
    - Get popular ideas for NIFTY from page 1 to 2:
      get_ideas("NIFTY", 1, 2, "popular")

    Note :
    - to avoid extra time for sraping recomanded 1-3 page for latest and popular ideas.

    Note: The function may require a TRADINGVIEW_JWT_TOKEN environment variable to be set for private API access.
    """
    try:
        # Validate parameters explicitly using centralized validators
        symbol = validate_symbol(symbol)

        result = fetch_ideas(
            symbol=symbol,
            startPage=startPage,
            endPage=endPage,
            sort=sort
        )

        return result
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "ideas": [],
            "help": "Please check the parameter values and try again."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "ideas": [],
            "help": "An unexpected error occurred. Please verify your inputs and try again."
        }


@mcp.tool
def get_option_chain_analysis(
    symbol: Annotated[str, Field(
        description="Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY'). Required.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[str, Field(
        description=(
            "Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. "
            f"Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format."
        ),
        min_length=2,
        max_length=30
    )],
    expiry_date: Annotated[Optional[Union[int, str]], Field(
        description=(
            "Option expiry date specification. Three modes supported:\n"
            "1. None (default): Fetches and groups data for ALL available expiry dates\n"
            "2. 'latest' (string): Fetches data for the NEAREST upcoming expiry date only\n"
            "3. Integer (YYYYMMDD format): Fetches data for that specific expiry date (e.g., 20251202, 20251225)\n\n"
            "Examples:\n"
            "- expiry_date=None → Returns all expiries grouped\n"
            "- expiry_date='latest' → Returns only the nearest upcoming expiry\n"
            "- expiry_date=20251202 → Returns only options expiring on Dec 2, 2025"
        )
    )] = None,
    top_n: Annotated[int, Field(
        description=(
            "Number of strikes to return above and below the current spot price (default: 5, max: 100).\n"
            "For example, if top_n=5:\n"
            "- Returns 5 ITM (In-The-Money) strikes below spot price\n"
            "- Returns 5 OTM (Out-of-The-Money) strikes at/above spot price\n"
            "Total strikes returned: top_n * 2 (one set below, one set above spot)"
        ),
        ge=1,
        le=100
    )] = 5
) -> dict:
    """
    Get comprehensive option chain analysis with complete Greeks (Delta, Gamma, Theta, Vega, Rho), 
    Implied Volatility (IV), and detailed strike-by-strike analytics for options trading.
    
    This function provides real-time option chain data from TradingView including:
    
    **Data Included:**
    - Current spot price of the underlying instrument
    - ITM (In-The-Money) strikes: Options below current spot price
    - OTM (Out-of-The-Money) strikes: Options at or above current spot price
    - Both CALL and PUT options for each strike
    
    **Greeks Provided for Each Option:**
    - Delta: Measures option price change per $1 move in underlying (range: 0 to 1 for calls, -1 to 0 for puts)
    - Gamma: Measures rate of change of delta per $1 move in underlying
    - Theta: Measures time decay - option value loss per day (always negative)
    - Vega: Measures sensitivity to volatility changes - price change per 1% volatility change
    - Rho: Measures sensitivity to interest rate changes per 1% rate change
    
    **Implied Volatility (IV) Data:**
    - Overall IV: Market's expectation of future volatility
    - Bid IV: Implied volatility at bid price
    - Ask IV: Implied volatility at ask price
    
    **Additional Metrics:**
    - Bid/Ask prices for each option
    - Theoretical option price (theo_price)
    - Intrinsic value: In-the-money amount (profit if exercised now)
    - Time value: Premium paid above intrinsic value
    - ATM (At-The-Money) strike identification
    - Aggregate analytics: Total call delta, total put delta, net delta exposure
    - TradingView symbol for each option (format: NSE:NIFTY251202C25700)
    
    **Parameters:**
    - symbol (str): Underlying instrument symbol (e.g., 'NIFTY', 'BANKNIFTY', 'RELIANCE')
    - exchange (str): Exchange where options trade (e.g., 'NSE' for National Stock Exchange of India)
    - expiry_date (None|str|int): 
        * None → Returns ALL expiry dates grouped together
        * 'latest' → Returns only the NEAREST upcoming expiry
        * Integer (YYYYMMDD) → Returns specific expiry (e.g., 20251202 for Dec 2, 2025)
    - top_n (int): Number of strikes above AND below spot to return (default: 5, max: 100)
                   Example: top_n=5 returns 5 ITM + 5 OTM = 10 total strikes
    
    **Return Structure:**
    
    For specific expiry (when expiry_date is integer or 'latest'):
    ```
    {
        'success': True,
        'spot_price': 25877.85,
        'expiry': 20251104,
        'itm_strikes': [  # Strikes below spot
            {
                'strike': 25700,
                'call': {
                    'symbol': 'NSE:NIFTY251104C25700',
                    'delta': 0.7547, 'gamma': 0.0002, 'theta': -12.45, 
                    'vega': 15.32, 'rho': 8.21,
                    'iv': 0.0834,  # 8.34% implied volatility
                    'bid_iv': 0.0831, 'ask_iv': 0.0837,
                    'bid': 175.5, 'ask': 178.0,
                    'theo_price': 176.75,
                    'intrinsic_value': 177.85,
                    'time_value': -1.10
                },
                'put': { ... similar structure ... }
            },
            ...
        ],
        'otm_strikes': [  # Strikes at or above spot
            { ... same structure as itm_strikes ... }
        ],
        'analytics': {
            'atm_strike': 25900,
            'total_call_delta': 12.4632,
            'total_put_delta': -8.2341,
            'net_delta': 4.2291,
            'total_strikes': 45
        }
    }
    ```
    
    For all expiries (when expiry_date is None):
    ```
    {
        'success': True,
        'spot_price': 25877.85,
        'expiries': {
            20251104: { 'itm_strikes': [...], 'otm_strikes': [...], 'analytics': {...} },
            20251111: { 'itm_strikes': [...], 'otm_strikes': [...], 'analytics': {...} },
            ...
        }
    }
    ```
    
    **Example Usage:**
    
    1. Get latest expiry with 10 strikes in each direction:
       `get_option_chain_analysis('NIFTY', 'NSE', 'latest', 10)`
    
    2. Get specific expiry (December 2, 2025) with 5 strikes:
       `get_option_chain_analysis('NIFTY', 'NSE', 20251202, 5)`
    
    3. Get all available expiries with 3 strikes each:
       `get_option_chain_analysis('NIFTY', 'NSE', None, 3)`
    
    **Use Cases:**
    - Options trading strategy planning (spreads, straddles, strangles)
    - Risk assessment using Greeks (delta hedging, gamma scalping)
    - Volatility analysis and trading
    - Identifying support/resistance levels via option OI and Greeks
    - Real-time options pricing and valuation
    
    **Note:** This function returns real-time data from TradingView. Greeks and IV are calculated 
    using standard options pricing models. All monetary values reflect current market conditions.
    """
    try:
        # Validate parameters
        from .validators import validate_exchange, validate_symbol
        
        exchange = validate_exchange(exchange)
        symbol = validate_symbol(symbol)
        
        result = process_option_chain_with_analysis(
            symbol=symbol,
            exchange=exchange,
            expiry_date=expiry_date,
            top_n=top_n
        )
        
        return result
        
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }


def main():
    """Run the MCP server."""
    print("🚀 Starting TradingView MCP Server...")
    print("📊 Available tools:")
    print("   - get_historical_data: Fetch OHLCV data with indicators")
    print("   - get_news_headlines: Get latest news headlines")
    print("   - get_news_content: Fetch full news articles")
    print("   - get_all_indicators: Get current values for all technical indicators")
    print("   - get_ideas: Get trading ideas from TradingView community")
    print("   - get_option_chain_analysis: Get option chain with Greeks, IV, and strike analysis")
    print("\n⚡ Server is ready!")
    mcp.run()


if __name__ == "__main__":
    main()