"""
FastMCP server for TradingView data scraping.
Provides tools for fetching historical data, news headlines, and news content.
"""

from typing import Annotated, List, Optional, Literal
from pydantic import Field
from fastmcp import FastMCP
from dotenv import load_dotenv
import json

from .tradingview_tools import (
    fetch_historical_data,
    fetch_news_headlines,
    fetch_news_content
)
from .tradingview_tools import fetch_all_indicators, fetch_trading_analysis
from .validators import (
    VALID_EXCHANGES, VALID_TIMEFRAMES, VALID_NEWS_PROVIDERS,
    VALID_AREAS, ValidationError,INDICATOR_MAPPING
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
        description=f"List of technical indicators to include. Options: {', '.join(INDICATOR_MAPPING.keys())}. Example: ['RSI', 'MACD']. Leave empty for no indicators.",
        max_length=2
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
def get_trading_analysis(
    symbol: Annotated[str, Field(
        description="Trading symbol/ticker (e.g., 'AAPL', 'NIFTY', 'TSLA'). Required.",
        min_length=1,
        max_length=20
    )],
    exchange: Annotated[str, Field(
        description=(
            "Stock exchange name (e.g., 'NASDAQ', 'NSE', 'NYSE'). Must be one of the valid exchanges. "
            f"Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format."
        ),
        min_length=2,
        max_length=30
    )],
    market: Annotated[Literal['america', 'india', 'crypto', 'forex', 'bond', 'futures'], Field(
        description="Market region to search in. Options: america, india, crypto, forex, bond, futures"
    )] = 'america'
) -> dict:
    """
    Get comprehensive trading analysis for a stock including fundamentals, technicals, and sentiment.
    
    This tool provides an extensive analysis covering multiple aspects of a stock:
    - Basic company information (name, sector, industry)
    - Price and volume data (current prices, trading volume, relative volume)
    - Performance metrics (1D, 1W, 1M, 3M, 6M, YTD, 1Y, 5Y returns)
    - Fundamental health (P/E, P/B, debt ratios, profitability metrics)
    - Dividend information (yield, payout ratio, dividends per share)
    - Risk and volatility measures (beta, ATR, volatility across timeframes)
    - Technical indicators (RSI, MACD, Stochastic, ADX, momentum indicators)
    - Moving averages (SMA and EMA for 10, 20, 50, 100, 200 periods)
    - Analyst recommendations and technical signal consensus
    - Company details (employees, shares outstanding)
    
    Parameters:
    - symbol (str): Stock ticker symbol (e.g., 'AAPL' for Apple Inc.)
    - exchange (str): Exchange where the stock is traded (e.g., 'NASDAQ', 'NSE')
    - market (str): Market region - 'america' for US stocks, 'india' for Indian stocks, etc.
    
    Returns:
    - success (bool): Whether the analysis was successfully retrieved
    - data (dict): Organized analysis data with sections for different metric categories
    - metadata (dict): Information about the request and data quality
    - message (str): Error description if success is False
    
    Example usage:
    - US stock: get_trading_analysis('AAPL', 'NASDAQ', 'america')
    - Indian stock: get_trading_analysis('NIFTY', 'NSE', 'india')
    - Crypto: get_trading_analysis('BTCUSD', 'BINANCE', 'crypto')
    
    Note: The function organizes data into logical categories (fundamentals, technicals, 
    performance, etc.) for easier analysis and decision-making.
    """
    try:
        # Validate parameters explicitly using centralized validators
        from .validators import validate_exchange, validate_symbol
        
        exchange = validate_exchange(exchange)
        symbol = validate_symbol(symbol)
        
        result = fetch_trading_analysis(symbol=symbol, exchange=exchange, market=market)
        return result
        
    except ValidationError as e:
        return {
            "success": False,
            "message": str(e),
            "data": {},
            "metadata": {
                "symbol": symbol,
                "exchange": exchange,
                "market": market
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "data": {},
            "metadata": {
                "symbol": symbol,
                "exchange": exchange,
                "market": market,
                "error_type": type(e).__name__
            }
        }


def main():
    """Run the MCP server."""
    print("🚀 Starting TradingView MCP Server...")
    print("📊 Available tools:")
    print("   - get_historical_data: Fetch OHLCV data with indicators")
    print("   - get_news_headlines: Get latest news headlines")
    print("   - get_news_content: Fetch full news articles")
    print("   - get_all_indicators: Get current values for all technical indicators")
    print("   - get_trading_analysis: Get comprehensive trading analysis (fundamentals, technicals, sentiment)")
    print("\n⚡ Server is ready!")
    mcp.run()


if __name__ == "__main__":
    main()