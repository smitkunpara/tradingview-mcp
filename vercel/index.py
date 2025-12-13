from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os
from toon import encode as toon_encode
from src.tradingview_mcp.tradingview_tools import (
    fetch_historical_data,
    fetch_news_headlines,
    fetch_news_content,
    fetch_all_indicators,
    fetch_ideas,
    fetch_minds,
    process_option_chain_with_analysis
)
from src.tradingview_mcp.validators import (
    ValidationError, 
    validate_symbol,
    validate_exchange
)
from src.tradingview_mcp.config import settings
from .models import (
    HistoricalDataRequest,
    NewsHeadlinesRequest,
    NewsContentRequest,
    AllIndicatorsRequest,
    IdeasRequest,
    MindsRequest,
    OptionChainGreeksRequest
)
# Load environment variables
load_dotenv()

# Define header schemes
admin_header_scheme = APIKeyHeader(name="X-Admin-Key", auto_error=False)
client_header_scheme = APIKeyHeader(name="X-Client-Key", auto_error=False)

async def verify_admin(key: str = Security(admin_header_scheme)):
    """Only allows access if X-Admin-Key matches .env"""
    if key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid Admin Key")
    return key

async def verify_client(key: str = Security(client_header_scheme)):
    """Only allows access if X-Client-Key matches .env"""
    if key != settings.CLIENT_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid Client Key")
    return key


vercel_backend_url = os.getenv("VERCEL_URL",None)
if vercel_backend_url:
    print(f"🌐 Vercel backend URL set to: {vercel_backend_url}")
app = FastAPI(
    title="TradingView HTTP API",
    description="REST API for TradingView data scraping tools",
    version="1.0.0",
    servers=[{"url": vercel_backend_url}] if vercel_backend_url else None
)

# Add CORS middleware to handle cross-origin requests from the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Chrome extension
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"]   # Allow all headers including X-Admin-Key
)


# API Endpoints
# Each endpoint corresponds to an MCP tool, with the same logic and error handling

@app.get("/health")
async def health_check():
    """Health check endpoint - no authentication required"""
    return {"status": "healthy", "service": "TradingView HTTP API"}


@app.post("/historical-data", dependencies=[Depends(verify_client)])
async def get_historical_data_endpoint(request: HistoricalDataRequest):
    """
    Fetch historical OHLCV data with technical indicators from TradingView.
    Returns candles with timestamps in IST. Requires internet connection.
    """

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
        
        # Encode result in TOON format for efficiency
        toon_data = toon_encode(result)
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/news-headlines", dependencies=[Depends(verify_client)])
async def get_news_headlines_endpoint(request: NewsHeadlinesRequest):
    """
    Scrape latest news headlines from TradingView for a specific symbol.
    Returns headlines with title, provider, and story paths for full content.
    """
    try:
        # Call the core function - pass cookie directly
        headlines = fetch_news_headlines(
            symbol=request.symbol,
            exchange=request.exchange,
            provider=request.provider,
            area=request.area,
            cookie=request.cookie
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


@app.post("/news-content", dependencies=[Depends(verify_client)])
async def get_news_content_endpoint(request: NewsContentRequest):
    """
    Fetch full news article content using story paths from headlines.
    Returns article title and body text. May return partial results.
    """
    try:
        # Call the core function - pass cookie directly
        articles = fetch_news_content(request.story_paths, cookie=request.cookie)

        # Encode in TOON format
        toon_data = toon_encode({"articles": articles})
        return {"data": toon_data}

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news content: {str(e)}")


@app.post("/all-indicators", dependencies=[Depends(verify_client)])
async def get_all_indicators_endpoint(request: AllIndicatorsRequest):
    """
    Return current values for all available technical indicators for a symbol.
    Provides latest snapshot, not historical series. Requires TRADINGVIEW_COOKIE.
    """
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


@app.post("/ideas", dependencies=[Depends(verify_client)])
async def get_ideas_endpoint(request: IdeasRequest):
    """
    Scrape trading ideas from TradingView for a specific symbol.
    Returns ideas with title, author, and content. Supports pagination and sorting.
    """
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

        # Call the core function - pass cookie directly
        result = fetch_ideas(
            symbol=symbol,
            startPage=startPage,
            endPage=endPage,
            sort=request.sort,
            cookie=request.cookie
        )

        # Encode in TOON format
        toon_data = toon_encode(result)
        return {"data": toon_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/minds", dependencies=[Depends(verify_client)])
async def get_minds_endpoint(request: MindsRequest):
    """
    Get community discussions (Minds) from TradingView for a specific symbol.
    Returns structured discussion data with author, text, likes, and comments.
    """
    try:
        limit = None
        if request.limit is not None:
            try:
                limit = int(request.limit) if isinstance(request.limit, str) else request.limit
                if limit <= 0:
                    raise ValidationError(f"limit must be a positive integer, got {limit}")
            except ValueError:
                raise ValidationError("limit must be a valid integer")

        symbol = validate_symbol(request.symbol)
        exchange = validate_exchange(request.exchange)

        result = fetch_minds(
            symbol=symbol,
            exchange=exchange,
            limit=limit,
            cookie=request.cookie
        )

        toon_data = toon_encode(result)
        return {"data": toon_data}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/option-chain-greeks", dependencies=[Depends(verify_client)])
async def get_option_chain_greeks_endpoint(request: OptionChainGreeksRequest):
    """
    Fetches real-time option chain with full Greeks, IV, and analytics.
    Returns strikes with bid/ask, theo prices, delta/gamma/theta/vega/rho, and IV data.
    """
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


@app.get("/privacy-policy", include_in_schema=False)
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


@app.get("/", include_in_schema=False)
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

@app.post("/update-cookies", include_in_schema=False, dependencies=[Depends(verify_admin)])
async def update_cookies(request: dict):
    """
    Receives raw cookies from extension, validates them, and updates server config.
    """
    try:
        raw_cookies = request.get("cookies", [])
        source = request.get("source", "unknown")
        
        if not raw_cookies:
            return {"success": False, "message": "No cookies provided in payload"}

        print(f"📥 Received {len(raw_cookies)} cookies from {source}")

        # 1. CONSTRUCT COOKIE STRING
        # We accept all cookies provided by the extension to ensure we have the full session
        cookie_parts = []
        for c in raw_cookies:
            # Basic cleaning
            name = c.get('name')
            value = c.get('value')
            if name and value:
                cookie_parts.append(f"{name}={value}")
        
        new_cookie_string = "; ".join(cookie_parts)
        print("🕵️ Verifying new session...")
        
        
        try:
            # Attempt to fetch a simple data point (like ideas or indicators)
            # This triggers the JWT extraction and HTTP request using the new cookie
            test_result = fetch_ideas("BTCUSD", startPage=1, endPage=1, cookie=new_cookie_string)
            
            # Check if the result indicates a success (fetched data)
            # If the cookie is bad, fetch_ideas typically returns empty or raises an error in auth
            if isinstance(test_result, dict) and test_result.get('success') is False:
                 raise ValueError("Validation request returned failure.")
            
            print("✅ Cookie Verification Successful!")
            # Update the server's cookie setting
            settings.update_cookie(new_cookie_string)
            return {
                "success": True, 
                "message": "Cookies verified and updated successfully.",
                "count": len(cookie_parts)
            }

        except Exception as e:
            print(f"❌ Verification Failed: {str(e)}")
            return {
                "success": False, 
                "message": f"Cookie validation failed: {str(e)}. Reverted to previous session."
            }

    except Exception as e:
        return {"success": False, "message": f"Server error processing cookies: {str(e)}"}


def main():
    """
    Main function to run the HTTP server.
    
    Starts the uvicorn server on host 0.0.0.0 and port 4589.
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
    print("\n🌐 Server running on http://localhost:4589")
    print("📖 API docs available at http://localhost:4589/docs")
    print("\n⚡ Server is ready!")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=4589)


if __name__ == "__main__":
    main()