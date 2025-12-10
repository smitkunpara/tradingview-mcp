"""
HTTP server for TradingView data scraping.
Provides REST API endpoints for fetching historical data, news headlines, news content, indicators, ideas, and option chains.
This server exposes the same functionality as the MCP server in main.py, but over HTTP for remote access.


The server uses FastAPI to create RESTful endpoints that mirror the MCP tools.
Each endpoint accepts JSON payloads with the same parameters as the corresponding MCP tool,
and returns the same TOON-encoded response data for consistency.


Environment Variables:
- TRADINGVIEW_COOKIE: Required for authentication with TradingView APIs. Set this in your .env file.


Dependencies:
- fastapi: Web framework for building the API
- uvicorn: ASGI server to run the FastAPI app
- pydantic: Data validation and serialization
- python-dotenv: Load environment variables from .env file
- toon: Efficient data encoding for responses
- Internal modules: tradingview_tools, validators


Usage:
Run this script directly: python http_main.py
The server will start on http://localhost:8000 by default.
Use tools like curl or Postman to interact with the endpoints.


API Endpoints:
- POST /historical-data: Fetch historical OHLCV data with indicators
- POST /news-headlines: Get latest news headlines for a symbol
- POST /news-content: Fetch full content of news articles
- POST /all-indicators: Get current values for all technical indicators
- POST /ideas: Scrape trading ideas from TradingView
- POST /option-chain-greeks: Get option chain with Greeks and analytics


All endpoints return TOON-encoded JSON responses for token efficiency, same as MCP tools.
"""


from typing import Annotated, List, Optional, Literal, Union
from pydantic import Field, BaseModel
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import uvicorn
import json
import os
from toon import encode as toon_encode


from src.tradingview_mcp.tradingview_tools import (
    fetch_historical_data,
    fetch_news_headlines,
    fetch_news_content,
    fetch_all_indicators,
    fetch_ideas,
    process_option_chain_with_analysis
)
from src.tradingview_mcp.validators import (
    VALID_EXCHANGES, VALID_TIMEFRAMES, VALID_NEWS_PROVIDERS,
    VALID_AREAS, ValidationError, INDICATOR_MAPPING, validate_symbol
)


# Load environment variables from .env file
# This ensures TRADINGVIEW_COOKIE and other secrets are loaded
load_dotenv()


# Initialize FastAPI application
vercel_backend_url = os.getenv("VERCEL_URL",None)
if vercel_backend_url:
    print(f"🌐 Vercel backend URL set to: {vercel_backend_url}")
# This creates the web server instance that will handle HTTP requests
app = FastAPI(
    title="TradingView HTTP API",
    description="REST API for TradingView data scraping tools",
    version="1.0.0",
    servers=[{"url": vercel_backend_url}] if vercel_backend_url else None
)


# Pydantic models for request bodies
# These define the expected JSON structure for each endpoint's request body


class HistoricalDataRequest(BaseModel):
    """
    Request model for historical data endpoint.

    Attributes:
    - exchange: Stock exchange name (e.g., 'NSE', 'NASDAQ', 'BINANCE'). Must be one of the valid exchanges like NSE, NASDAQ, BINANCE... Use uppercase format.
    - symbol: Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.
    - timeframe: Time interval for each candle. Options: 1m (1 minute), 5m, 15m, 30m, 1h (1 hour), 2h, 4h, 1d (1 day), 1w (1 week), 1M (1 month)
    - numb_price_candles: Number of historical candles to fetch (1-5000). Accepts int or str (e.g., 100 or '100'). More candles = longer history. E.g., 100 for last 100 periods.
    - indicators: List of technical indicators to include. Options: RSI, MACD, CCI, BB. Leave empty for no indicators.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE', 'NASDAQ', 'BINANCE'). Must be one of the valid exchanges like {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field(..., description="Time interval for each candle. Options: 1m (1 minute), 5m, 15m, 30m, 1h (1 hour), 2h, 4h, 1d (1 day), 1w (1 week), 1M (1 month)")
    numb_price_candles: Union[int, str] = Field(..., description="Number of historical candles to fetch (1-5000). Accepts int or str (e.g., 100 or '100'). More candles = longer history. E.g., 100 for last 100 periods.")
    indicators: List[str] = Field(default=[], description=f"List of technical indicators to include. Options: {', '.join(INDICATOR_MAPPING.keys())}. Example: ['RSI', 'MACD', 'CCI', 'BB']. Leave empty for no indicators.")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class NewsHeadlinesRequest(BaseModel):
    """
    Request model for news headlines endpoint.

    Attributes:
    - symbol: Trading symbol for news (e.g., 'NIFTY', 'AAPL'). Max 20 characters.
    - exchange: Optional exchange filter. Must be in VALID_EXCHANGES if provided.
    - provider: News provider filter. One of VALID_NEWS_PROVIDERS or 'all'. Default 'all'.
    - area: Geographical area filter. One of: 'world', 'americas', 'europe', 'asia', 'oceania', 'africa'. Default 'asia'.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol for news (e.g., 'NIFTY', 'AAPL', 'BTC'). Required. Search online for correct symbol.")
    exchange: Optional[str] = Field(None, min_length=2, max_length=30, description=f"Optional exchange filter. One of: {', '.join(VALID_EXCHANGES)}... Leave empty for all exchanges.")
    provider: str = Field("all", min_length=3, max_length=20, description=f"News provider filter. Options: {', '.join(VALID_NEWS_PROVIDERS)}... or 'all' for all providers.")
    area: Literal['world', 'americas', 'europe', 'asia', 'oceania', 'africa'] = Field('asia', description="Geographical area filter for news. Default is 'asia'.")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class NewsContentRequest(BaseModel):
    """
    Request model for news content endpoint.

    Attributes:
    - story_paths: List of story paths from news headlines. Each must start with '/news/'. Max 20 items.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    story_paths: List[str] = Field(..., min_items=1, max_items=20, description="List of story paths from news headlines. Each path must start with '/news/'. Get these from get_news_headlines() results.")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class AllIndicatorsRequest(BaseModel):
    """
    Request model for all indicators endpoint.

    Attributes:
    - symbol: Trading symbol/ticker (e.g., 'NIFTY', 'AAPL'). Max 20 characters.
    - exchange: Stock exchange name. Must be in VALID_EXCHANGES.
    - timeframe: Time interval for indicator snapshot. One of VALID_TIMEFRAMES. Default '1m'.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Required.")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field('1m', description=f"Time interval for indicator snapshot. Valid options: {', '.join(VALID_TIMEFRAMES)}")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class IdeasRequest(BaseModel):
    """
    Request model for ideas endpoint.

    Attributes:
    - symbol: Trading symbol/ticker (e.g., 'NIFTY', 'AAPL'). Max 20 characters.
    - startPage: Starting page number (1-10). Can be int or str. Default 1.
    - endPage: Ending page number (1-10, >= startPage). Can be int or str. Default 1.
    - sort: Sorting order. 'popular' or 'recent'. Default 'popular'.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.")
    startPage: Union[int, str] = Field(1, description="Starting page number for scraping ideas. Accepts int or str (e.g., 1 or '1').")
    endPage: Union[int, str] = Field(1, description="Ending page number for scraping ideas. Accepts int or str (e.g., 1 or '1').")
    sort: Literal['popular', 'recent'] = Field('popular', description="Sorting order for ideas. 'popular' for most liked, 'recent' for latest.")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class OptionChainGreeksRequest(BaseModel):
    """
    Request model for option chain Greeks endpoint.

    Attributes:
    - symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY'). Max 20 characters.
    - exchange: Stock exchange name. Must be in VALID_EXCHANGES.
    - expiry_date: Optional expiry date. None for all, 'latest' for nearest, or YYYYMMDD int/str for specific.
    - top_n: Strikes per side (1-20). Can be int or str. Default 5.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    symbol: str = Field(..., min_length=1, max_length=20, description="Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY'). Required.")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    expiry_date: Optional[Union[int, str]] = Field(None, description="Option expiry date:\n- None (default): ALL expiries grouped by date\n- 'latest': NEAREST expiry only\n- int YYYYMMDD (e.g., 20251202): SPECIFIC expiry")
    top_n: Union[int, str] = Field(5, description="Strikes per side (ITM below + OTM >= spot). Default 3, max 20.\nE.g., top_n=5 → 5 ITM + 5 OTM = 10 strikes total.")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


# API Endpoints
# Each endpoint corresponds to an MCP tool, with the same logic and error handling


@app.post("/historical-data")
async def get_historical_data_endpoint(request: HistoricalDataRequest):
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
      POST /historical-data with {"exchange": "BINANCE", "symbol": "BTCUSD", "timeframe": "1m", "numb_price_candles": 100, "indicators": ["RSI"]}
    
    Note: Requires active internet connection to fetch data from TradingView.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Validate numb_price_candles parameter
        try:
            numb_price_candles = int(request.numb_price_candles) if isinstance(request.numb_price_candles, str) else request.numb_price_candles
            if not (1 <= numb_price_candles <= 5000):
                raise ValidationError(f"numb_price_candles must be between 1 and 5000, got {numb_price_candles}")
        except ValueError:
            raise ValidationError("numb_price_candles must be a valid integer")


        # Call the core function from tradingview_tools
        result = fetch_historical_data(
            exchange=request.exchange,
            symbol=request.symbol,
            timeframe=request.timeframe,
            numb_price_candles=numb_price_candles,
            indicators=request.indicators
        )

        #cleart the export folder
        if os.path.exists("export"):
            import shutil
            shutil.rmtree("export")
        
        # Encode result in TOON format for efficiency
        toon_data = toon_encode(result)
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.post("/news-headlines")
async def get_news_headlines_endpoint(request: NewsHeadlinesRequest):
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
      POST /news-headlines with {"symbol": "NIFTY", "exchange": "NSE", "provider": "all", "area": "asia"}
    - Get crypto news for Bitcoin:
      POST /news-headlines with {"symbol": "BTC", "provider": "coindesk", "area": "world"}
    
    Use the storyPath from results with /news-content to fetch full articles.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Call the core function
        headlines = fetch_news_headlines(
            symbol=request.symbol,
            exchange=request.exchange,
            provider=request.provider,
            area=request.area
        )

        if not headlines:
            return {"data": "headlines[0]:"}


        # Encode in TOON format
        toon_data = toon_encode({"headlines": headlines})
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.post("/news-content")
async def get_news_content_endpoint(request: NewsContentRequest):
    """
    Fetch full news article content using story paths from headlines.
    
    Retrieves the complete article text for news stories using the story paths
    obtained from /news-headlines. Processes multiple articles in a single
    request and extracts the main text content.
    
    Returns a list of articles, each containing:
    - success: Whether content was fetched successfully
    - title: Article title
    - body: Full article text content
    - story_path: Original story path used
    - error: Error message if fetch failed (only on failure)
    
    Example usage:
    1. First get headlines: POST /news-headlines with {"symbol": "AAPL"}
    2. Extract story paths from response
    3. Get full content: POST /news-content with {"story_paths": ["/news/story1", "/news/story2"]}
    
    Note: Some articles may fail to load due to source restrictions.
    The function will still return partial results for successful fetches.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Call the core function
        articles = fetch_news_content(request.story_paths)

        # Encode in TOON format
        toon_data = toon_encode({"articles": articles})
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news content: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.post("/all-indicators")
async def get_all_indicators_endpoint(request: AllIndicatorsRequest):
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
    - POST /all-indicators with {"symbol": "NIFTY", "exchange": "NSE", "timeframe": "1m"}

    Note: The underlying scraper requires TRADINGVIEW_COOKIE environment variable 
    to be set for authentication. JWT tokens are automatically generated from cookies.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Validate parameters using centralized validators
        from src.tradingview_mcp.validators import validate_exchange, validate_timeframe, validate_symbol


        exchange = validate_exchange(request.exchange)
        symbol = validate_symbol(request.symbol)
        timeframe = validate_timeframe(request.timeframe)


        # Call the core function
        result = fetch_all_indicators(exchange=exchange, symbol=symbol, timeframe=timeframe)


        # Encode in TOON format
        toon_data = toon_encode(result)
        return {"data": toon_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.post("/ideas")
async def get_ideas_endpoint(request: IdeasRequest):
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
      POST /ideas with {"symbol": "NIFTY", "startPage": 1, "endPage": 2, "sort": "popular"}

    Note :
    - to avoid extra time for sraping recomanded 1-3 page for latest and popular ideas.

    Note: The function requires TRADINGVIEW_COOKIE environment variable to be set 
    for authentication. JWT tokens are automatically generated from cookies as needed.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Validate startPage
        try:
            startPage = int(request.startPage) if isinstance(request.startPage, str) else request.startPage
            if not (1 <= startPage <= 10):
                raise ValidationError(f"startPage must be between 1 and 10, got {startPage}")
        except ValueError:
            raise ValidationError("startPage must be a valid integer")


        # Validate endPage
        try:
            endPage = int(request.endPage) if isinstance(request.endPage, str) else request.endPage
            if not (1 <= endPage <= 10):
                raise ValidationError(f"endPage must be between 1 and 10, got {endPage}")
            if endPage < startPage:
                raise ValidationError(f"endPage ({endPage}) must be greater than or equal to startPage ({startPage})")
        except ValueError:
            raise ValidationError("endPage must be a valid integer")


        # Validate symbol
        symbol = validate_symbol(request.symbol)


        # Call the core function
        result = fetch_ideas(
            symbol=symbol,
            startPage=startPage,
            endPage=endPage,
            sort=request.sort
        )


        # Encode in TOON format
        toon_data = toon_encode(result)
        return {"data": toon_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.post("/option-chain-greeks")
async def get_option_chain_greeks_endpoint(request: OptionChainGreeksRequest):
    """
Fetches real-time TradingView option chain with FULL Greeks (delta, gamma, theta, vega, rho),
IV (overall/bid/ask), bid/ask/theo prices, intrinsic/time values for CALL/PUT at key strikes.

**Structure (per expiry):**
- spot_price: Current underlying price
- itm_strikes: List[<top_n> strikes < spot] with call/put details
- otm_strikes: List[<top_n> strikes >= spot] with call/put details
- analytics: atm_strike, total_call_delta, total_put_delta, net_delta, total_strikes

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
- Latest expiry, 10 strikes/side: POST /option-chain-greeks with {"symbol": "NIFTY", "exchange": "NSE", "expiry_date": "latest", "top_n": 10}
- Specific expiry: POST /option-chain-greeks with {"symbol": "NIFTY", "exchange": "NSE", "expiry_date": 20251202, "top_n": 5}
- All expiries: POST /option-chain-greeks with {"symbol": "NIFTY", "exchange": "NSE", "expiry_date": null, "top_n": 3}

**Use cases:** Build straddles/strangles, delta-hedge, IV crush trades, gamma scalps, spot support levels.
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Validate top_n
        try:
            top_n = int(request.top_n) if isinstance(request.top_n, str) else request.top_n
            if not (1 <= top_n <= 20):
                raise ValidationError(f"top_n must be between 1 and 20, got {top_n}")
        except ValueError:
            raise ValidationError("top_n must be a valid integer")


        # Validate parameters
        from src.tradingview_mcp.validators import validate_exchange, validate_symbol

        exchange = validate_exchange(request.exchange)
        symbol = validate_symbol(request.symbol)

        # Call the core function
        result = process_option_chain_with_analysis(
            symbol=symbol,
            exchange=exchange,
            expiry_date=request.expiry_date,
            top_n=top_n
        )

        # Encode in TOON format
        toon_data = toon_encode(result)
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Restore original cookie
        if request.cookie:
            if original_cookie is not None:
                os.environ["TRADINGVIEW_COOKIE"] = original_cookie
            else:
                os.environ.pop("TRADINGVIEW_COOKIE", None)


@app.get("/privacy-policy")
async def get_privacy_policy():
    """
    Privacy Policy endpoint.

    Returns the privacy policy and disclaimer for the API.
    """
    return {
        "privacy_policy": """
        Privacy Policy for TradingView HTTP API Server

        This application and its associated API are created solely for learning and improving purposes. All data, tools, and information provided through this service are intended for educational use only.

        Important Disclaimer:
        This is not financial advice. The data and tools provided by this API should not be used as the basis for any financial decisions, investments, or trading activities. Users are responsible for their own financial decisions and should consult with qualified financial advisors before making any investment choices.

        Data Collection and Usage:
        - This API scrapes publicly available data from TradingView.
        - No personal user data is collected or stored by this service.
        - Authentication is handled via TradingView cookies, which are not stored on our servers.

        Liability:
        The creators and maintainers of this API are not liable for any losses, damages, or consequences arising from the use of this service or the data it provides.

        For any questions or concerns, please contact the repository owner.
        """
    }


@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns basic info about available endpoints.
    """
    return {
        "message": "TradingView HTTP API Server",
        "version": "1.0.0",
        "servers":[
            {"url": os.getenv("VERCEL_URL", "https://tradingview-mcp.vercel.app/")}
        ],
        "endpoints": [
            "/historical-data",
            "/news-headlines", 
            "/news-content",
            "/all-indicators",
            "/ideas",
            "/option-chain-greeks",
            "/privacy-policy"
        ]
    }


def main():
    """
    Main function to run the HTTP server.
    
    Starts the uvicorn server on host 0.0.0.0 and port 8000.
    This allows remote access to the API.
    """
    print("🚀 Starting TradingView HTTP API Server...")
    print("📊 Available endpoints:")
    print("   - POST /historical-data: Fetch OHLCV data with indicators")
    print("   - POST /news-headlines: Get latest news headlines")
    print("   - POST /news-content: Fetch full news articles")
    print("   - POST /all-indicators: Get current values for all technical indicators")
    print("   - POST /ideas: Get trading ideas from TradingView community")
    print("   - POST /option-chain-greeks: Get detailed option chain with full Greeks, IV & analytics")
    print("   - GET /privacy-policy: View privacy policy and disclaimer")
    print("   - GET /: API information")
    print("\n🌐 Server running on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    print("\n⚡ Server is ready!")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()