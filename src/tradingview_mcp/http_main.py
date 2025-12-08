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
    VALID_AREAS, ValidationError, INDICATOR_MAPPING, validate_symbol
)


# Load environment variables from .env file
# This ensures TRADINGVIEW_COOKIE and other secrets are loaded
load_dotenv()


# Initialize FastAPI application
# This creates the web server instance that will handle HTTP requests
app = FastAPI(
    title="TradingView HTTP API",
    description="REST API for TradingView data scraping tools",
    version="1.0.0",
    servers=[{"url": "https://4eb70c744992.ngrok-free.app"}]
)


# Pydantic models for request bodies
# These define the expected JSON structure for each endpoint's request body


class HistoricalDataRequest(BaseModel):
    """
    Request model for historical data endpoint.

    Attributes:
    - exchange: Stock exchange name (e.g., 'NSE', 'NASDAQ'). Must be uppercase and in VALID_EXCHANGES.
    - symbol: Trading symbol/ticker (e.g., 'NIFTY', 'AAPL'). Max 20 characters.
    - timeframe: Time interval for candles. One of: '1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'.
    - numb_price_candles: Number of historical candles to fetch (1-5000). Can be int or str.
    - indicators: List of technical indicators to include (optional). Options from INDICATOR_MAPPING.keys().
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name. Valid: {', '.join(VALID_EXCHANGES[:5])}...")
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field(..., description="Time interval for candles")
    numb_price_candles: Union[int, str] = Field(..., description="Number of candles (1-5000)")
    indicators: List[str] = Field(default=[], description=f"Technical indicators. Options: {', '.join(INDICATOR_MAPPING.keys())}")
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
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol for news")
    exchange: Optional[str] = Field(None, min_length=2, max_length=30, description=f"Optional exchange filter. Valid: {', '.join(VALID_EXCHANGES[:5])}...")
    provider: str = Field("all", min_length=3, max_length=20, description=f"News provider. Options: {', '.join(VALID_NEWS_PROVIDERS[:5])}... or 'all'")
    area: Literal['world', 'americas', 'europe', 'asia', 'oceania', 'africa'] = Field('asia', description="Geographical area filter")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


class NewsContentRequest(BaseModel):
    """
    Request model for news content endpoint.

    Attributes:
    - story_paths: List of story paths from news headlines. Each must start with '/news/'. Max 20 items.
    - cookie: TradingView cookie string for authentication (optional, uses env var if not provided).
    """
    story_paths: List[str] = Field(..., min_items=1, max_items=20, description="Story paths from get_news_headlines results. Each starts with '/news/'")
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
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Exchange name. Valid: {', '.join(VALID_EXCHANGES[:5])}...")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field('1m', description="Timeframe for indicators")
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
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker")
    startPage: Union[int, str] = Field(1, description="Starting page number (1-10)")
    endPage: Union[int, str] = Field(1, description="Ending page number (1-10, >= startPage)")
    sort: Literal['popular', 'recent'] = Field('popular', description="Sorting order for ideas")
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
    symbol: str = Field(..., min_length=1, max_length=20, description="Underlying symbol")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Exchange name. Valid: {', '.join(VALID_EXCHANGES[:5])}...")
    expiry_date: Optional[Union[int, str]] = Field(None, description="Expiry date: None (all), 'latest', or YYYYMMDD")
    top_n: Union[int, str] = Field(5, description="Strikes per side (1-20)")
    cookie: Optional[str] = Field(None, description="TradingView cookie string for authentication")


# API Endpoints
# Each endpoint corresponds to an MCP tool, with the same logic and error handling


@app.post("/historical-data")
async def get_historical_data_endpoint(request: HistoricalDataRequest):
    """
    Fetch historical OHLCV data with technical indicators.

    This endpoint mirrors the get_historical_data MCP tool.
    Accepts HistoricalDataRequest JSON and returns TOON-encoded response.

    Returns:
    - TOON-encoded dict with success, data, errors, metadata
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
    Get latest news headlines for a symbol.

    This endpoint mirrors the get_news_headlines MCP tool.
    Accepts NewsHeadlinesRequest JSON and returns TOON-encoded headlines.

    Returns:
    - TOON-encoded dict with headlines list
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
    Fetch full content of news articles.

    This endpoint mirrors the get_news_content MCP tool.
    Accepts NewsContentRequest JSON and returns TOON-encoded articles.

    Returns:
    - TOON-encoded dict with articles list
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
    Get current values for all technical indicators.

    This endpoint mirrors the get_all_indicators MCP tool.
    Accepts AllIndicatorsRequest JSON and returns TOON-encoded indicators.

    Returns:
    - TOON-encoded dict with success, data, message
    """
    # Handle cookie override
    original_cookie = os.environ.get("TRADINGVIEW_COOKIE")
    if request.cookie:
        os.environ["TRADINGVIEW_COOKIE"] = request.cookie

    try:
        # Validate parameters using centralized validators
        from .validators import validate_exchange, validate_timeframe, validate_symbol


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
    Scrape trading ideas from TradingView.

    This endpoint mirrors the get_ideas MCP tool.
    Accepts IdeasRequest JSON and returns TOON-encoded ideas.

    Returns:
    - TOON-encoded dict with success, ideas, count, message
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
    Get option chain with full Greeks and analytics.

    This endpoint mirrors the get_option_chain_greeks MCP tool.
    Accepts OptionChainGreeksRequest JSON and returns TOON-encoded option data.

    Returns:
    - TOON-encoded dict with success, spot_price, expiry data, strikes, analytics
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
        from .validators import validate_exchange, validate_symbol

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
            {"url": "https://4eb70c744992.ngrok-free.app"}
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