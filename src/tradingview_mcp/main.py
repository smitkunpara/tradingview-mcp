"""
FastMCP server for TradingView data scraping.
Provides tools for fetching historical data, news headlines, and news content.
"""

from typing import Annotated, List, Optional, Literal, Union
from pydantic import Field
from fastmcp import FastMCP
from dotenv import load_dotenv
import json
from toon import encode as toon_encode
import os

from .tradingview_tools import (
    fetch_historical_data,
    fetch_news_headlines,
    fetch_news_content,
    fetch_all_indicators,
    fetch_ideas,
    fetch_minds,
    process_option_chain_with_analysis
)
from .validators import (
    VALID_EXCHANGES, VALID_TIMEFRAMES, VALID_NEWS_PROVIDERS,
    VALID_AREAS, ValidationError,INDICATOR_MAPPING,
    validate_symbol,validate_exchange, validate_timeframe
)


# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("TradingView-MCP")


@mcp.tool
def get_historical_data(
    exchange: Annotated[str, Field(
        description=f"Stock exchange name (e.g., 'NSE', 'NASDAQ', 'BINANCE'). Must be one of the valid exchanges like {', '.join(VALID_EXCHANGES)}... Use uppercase format.",
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
    numb_price_candles: Annotated[Union[int, str], Field(
        description="Number of historical candles to fetch (1-5000). Accepts int or str (e.g., 100 or '100'). More candles = longer history. E.g., 100 for last 100 periods."
    )],
    indicators: Annotated[List[str], Field(
        description=(
            f"List of technical indicators to include. Options: {', '.join(INDICATOR_MAPPING.keys())}. "
            "Example: ['RSI', 'MACD', 'CCI', 'BB']. Leave empty for no indicators."
        )
    )] = []
) -> str:
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
    - Get last 100 1-minute candles for BTCUSD with RSI:
      get_historical_data("BINANCE", "BTCUSD", "1m", 100, ["RSI"])
    
    Note: Requires active internet connection to fetch data from TradingView.
    """
    try:
        # Validate numb_price_candles
        try:
            numb_price_candles = int(numb_price_candles) if isinstance(numb_price_candles, str) else numb_price_candles
            if not (1 <= numb_price_candles <= 5000):
                raise ValidationError(f"numb_price_candles must be between 1 and 5000, got {numb_price_candles}")
        except ValueError:
            raise ValidationError("numb_price_candles must be a valid integer")

        result = fetch_historical_data(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            numb_price_candles=numb_price_candles,
            indicators=indicators
        )
            
        # Encode the data in TOON format for token efficiency
        toon_data = toon_encode(result)

        return toon_data
    
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "data": [],
            "help": "Please check the parameter values and try again."
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": [],
            "help": "An unexpected error occurred. Please verify your inputs and try again."
        })


@mcp.tool
def get_news_headlines(
    symbol: Annotated[str, Field(
        description="Trading symbol for news (e.g., 'NIFTY', 'AAPL', 'BTC'). Required. Search online for correct symbol.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[Optional[str], Field(
        description=f"Optional exchange filter. One of: {', '.join(VALID_EXCHANGES)}... Leave empty for all exchanges.",
        min_length=2,
        max_length=30
    )] = None,
    provider: Annotated[str, Field(
        description=f"News provider filter. Options: {', '.join(VALID_NEWS_PROVIDERS)}... or 'all' for all providers.",
        min_length=3,
        max_length=20
    )] = "all",
    area: Annotated[Literal['world', 'americas', 'europe', 'asia', 'oceania', 'africa'], Field(
        description="Geographical area filter for news. Default is 'asia'."
    )] = 'asia'
) -> str:
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
            return "headlines[0]:"

        # Encode headlines in TOON format for token efficiency
        toon_data = toon_encode({"headlines": headlines})

        return toon_data
        
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "headlines": [],
            "help": f"Valid exchanges: {', '.join(VALID_EXCHANGES[:5])}..., "
                   f"Valid providers: {', '.join(VALID_NEWS_PROVIDERS[:5])}..., "
                   f"Valid areas: {', '.join(VALID_AREAS)}"
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Failed to fetch news: {str(e)}",
            "headlines": [],
            "help": "Please verify the symbol exists and try again."
        })


@mcp.tool
def get_news_content(
    story_paths: Annotated[List[str], Field(
        description="List of story paths from news headlines. Each path must start with '/news/'. Get these from get_news_headlines() results.",
        min_length=1,
        max_length=20
    )]
) -> str:
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
        
        # Encode articles in TOON format for token efficiency
        toon_data = toon_encode({"articles": articles})

        return toon_data
        
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "articles": [],
            "help": "Story paths must start with '/news/' and come from get_news_headlines() results"
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Failed to fetch news content: {str(e)}",
            "articles": [],
            "help": "Please verify the story paths are valid and try again"
        })


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
) -> str:
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

    Note: The underlying scraper requires TRADINGVIEW_COOKIE environment variable 
    to be set for authentication. JWT tokens are automatically generated from cookies.
    """
    try:
        exchange = validate_exchange(exchange)
        symbol = validate_symbol(symbol)
        timeframe = validate_timeframe(timeframe)

        result = fetch_all_indicators(exchange=exchange, symbol=symbol, timeframe=timeframe)
        toon_data = toon_encode(result)

        return toon_data
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "data": {}
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": {}
        })


@mcp.tool
def get_ideas(
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.",
        min_length=1,
        max_length=20
    )],
    startPage: Annotated[Union[int, str], Field(
        description="Starting page number for scraping ideas. Accepts int or str (e.g., 1 or '1')."
    )] = 1,
    endPage: Annotated[Union[int, str], Field(
        description="Ending page number for scraping ideas. Accepts int or str (e.g., 1 or '1')."
    )] = 1,
    sort: Annotated[Literal['popular', 'recent'], Field(
        description="Sorting order for ideas. 'popular' for most liked, 'recent' for latest."
    )] = 'popular'
) -> str:
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

    Note: The function requires TRADINGVIEW_COOKIE environment variable to be set 
    for authentication. JWT tokens are automatically generated from cookies as needed.
    """
    try:
        # Validate startPage
        try:
            startPage = int(startPage) if isinstance(startPage, str) else startPage
            if not (1 <= startPage <= 10):
                raise ValidationError(f"startPage must be between 1 and 10, got {startPage}")
        except ValueError:
            raise ValidationError("startPage must be a valid integer")

        # Validate endPage
        try:
            endPage = int(endPage) if isinstance(endPage, str) else endPage
            if not (1 <= endPage <= 10):
                raise ValidationError(f"endPage must be between 1 and 10, got {endPage}")
            if endPage < startPage:
                raise ValidationError(f"endPage ({endPage}) must be greater than or equal to startPage ({startPage})")
        except ValueError:
            raise ValidationError("endPage must be a valid integer")

        # Validate parameters explicitly using centralized validators
        symbol = validate_symbol(symbol)

        result = fetch_ideas(
            symbol=symbol,
            startPage=startPage,
            endPage=endPage,
            sort=sort
        )

        # Encode ideas in TOON format for token efficiency
        toon_data = toon_encode(result)

        return toon_data
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "ideas": [],
            "help": "Please check the parameter values and try again."
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "ideas": [],
            "help": "An unexpected error occurred. Please verify your inputs and try again."
        })


@mcp.tool
def get_minds(
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Required.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[str, Field(
        description=f"Stock exchange name (e.g., 'NSE', 'NASDAQ'). Must be one of the valid exchanges like {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.",
        min_length=2,
        max_length=30
    )],
    limit: Annotated[Optional[Union[int, str]], Field(
        description="Maximum number of discussions to retrieve from first page. If None, fetches all available. Accepts int or str (e.g., 100 or '100')."
    )] = None
) -> str:
    """
    Get community discussions (Minds) from TradingView for a specific symbol.

    Fetches community-generated discussions, questions, and sentiment from TradingView's 
    Minds feature. Returns structured discussion data including author, text, likes, and comments.

    Parameters:
    - symbol (str): Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD')
    - exchange (str): Stock exchange name (e.g., 'NSE', 'NASDAQ')
    - limit (int, optional): Maximum number of results from first page. If None, fetches all available

    Returns a dictionary containing:
    - status: 'success' or 'failed'
    - data: List of discussion items with author, text, likes, comments
    - total: Total number of results retrieved
    - symbol_info: Information about the symbol
    - pages: Number of pages retrieved (always 1)

    Example usage:
    - Get all discussions for Apple: get_minds("AAPL", "NASDAQ")
    - Get 50 discussions for Bitcoin: get_minds("BTCUSD", "BITSTAMP", 50)
    """
    try:
        if limit is not None:
            try:
                limit = int(limit) if isinstance(limit, str) else limit
                if limit <= 0:
                    raise ValidationError(f"limit must be a positive integer, got {limit}")
            except ValueError:
                raise ValidationError("limit must be a valid integer")

        symbol = validate_symbol(symbol)
        exchange = validate_exchange(exchange)

        result = fetch_minds(
            symbol=symbol,
            exchange=exchange,
            limit=limit
        )

        toon_data = toon_encode(result)

        return toon_data
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e),
            "data": [],
            "help": "Please verify symbol and exchange are valid."
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": [],
            "help": "An unexpected error occurred. Please verify your inputs and try again."
        })


@mcp.tool
def get_option_chain_greeks(
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
            "Option expiry date:\n"
            "- 'nearest' (default): NEAREST expiry only\n"
            "- 'all': ALL expiries grouped by date\n"
            "- int YYYYMMDD (e.g., 20251202): SPECIFIC expiry\n"
        )
    )] = 'nearest',
    no_of_ITM: Annotated[Union[int, str], Field(
        description=(
            "Number of In-The-Money strikes (below spot for calls, above for puts). Default 5, max 20."
        )
    )] = 5,
    no_of_OTM: Annotated[Union[int, str], Field(
        description=(
            "Number of Out-of-The-Money strikes (above spot for calls, below for puts). Default 5, max 20."
        )
    )] = 5
) -> str:
    """
Fetches real-time TradingView option chain with FULL Greeks (delta, gamma, theta, vega, rho),
IV (overall/bid/ask), bid/ask/theo prices, intrinsic/time values for CALL/PUT at key strikes.

**Structure (per expiry):**
- spot_price: Current underlying price
- data: List of options with call/put details
- analytics: atm_strike, total_call_delta, total_put_delta, net_delta, total_strikes
- available_expiries: List of all available expiry dates

**Per option details:**
```
{
  'symbol': 'NSE:NIFTY251104C25700',
  'bid': 175.5, 'ask': 178.0, 'theo_price': 176.75,
  'intrinsic_value': 177.85, 'time_value': -1.10,
  'delta': 0.7547, 'gamma': 0.0002, 'theta': -12.45,
  'vega': 15.32, 'rho': 8.21,
  'iv': 0.0834, 'bid_iv': 0.0831, 'ask_iv': 0.0837
}
```

**Returns:** TOON-encoded dict {success, spot_price, expiry/data, strikes, analytics}

**Examples:**
- Nearest expiry, 5 ITM + 5 OTM: `get_option_chain_greeks('NIFTY', 'NSE', 'nearest', 5, 5)`
- Specific expiry: `get_option_chain_greeks('NIFTY', 'NSE', 20251202, 5, 5)`
- All expiries: `get_option_chain_greeks('NIFTY', 'NSE', 'all', 3, 3)`
- Custom: `get_option_chain_greeks('NIFTY', 'NSE', 'nearest', 10, 5)` # 10 ITM, 5 OTM

**Use cases:** Build straddles/strangles, delta-hedge, IV crush trades, gamma scalps, spot support levels.
"""
    try:
        try:
            no_of_ITM = int(no_of_ITM) if isinstance(no_of_ITM, str) else no_of_ITM
            if not (1 <= no_of_ITM <= 20):
                raise ValidationError(f"no_of_ITM must be between 1 and 20, got {no_of_ITM}")
        except ValueError:
            raise ValidationError("no_of_ITM must be a valid integer")
        
        try:
            no_of_OTM = int(no_of_OTM) if isinstance(no_of_OTM, str) else no_of_OTM
            if not (1 <= no_of_OTM <= 20):
                raise ValidationError(f"no_of_OTM must be between 1 and 20, got {no_of_OTM}")
        except ValueError:
            raise ValidationError("no_of_OTM must be a valid integer")

        exchange = validate_exchange(exchange)
        symbol = validate_symbol(symbol)
        
        result = process_option_chain_with_analysis(
            symbol=symbol,
            exchange=exchange,
            expiry_date=expiry_date,
            no_of_ITM=no_of_ITM,
            no_of_OTM=no_of_OTM
        )
        # Encode option chain data in TOON format for token efficiency
        toon_data = toon_encode(result)

        return toon_data
        
    except ValidationError as e:
        return toon_encode({
            "success": False,
            "message": str(e)
        })
    except Exception as e:
        return toon_encode({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        })


def main():
    """Run the MCP server."""
    print("Starting TradingView MCP Server...")
    print("Available tools:")
    print("   - get_historical_data: Fetch OHLCV data with indicators")
    print("   - get_news_headlines: Get latest news headlines")
    print("   - get_news_content: Fetch full news articles")
    print("   - get_all_indicators: Get current values for all technical indicators")
    print("   - get_ideas: Get trading ideas from TradingView community")
    print("   - get_minds: Get community discussions from TradingView Minds")
    print("   - get_option_chain_greeks: Get detailed option chain with full Greeks, IV & analytics")
    print("\n Server is ready!")
    mcp.run()


if __name__ == "__main__":
    main()