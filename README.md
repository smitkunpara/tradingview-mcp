# TradingView MCP Server

A FastMCP server for scraping TradingView data including historical prices, technical indicators, and news.

## Installation

Using UV:
```bash
# Install dependencies
uv pip install -r requirements.txt

# Install the tradingview_scraper package (your existing package)
# uv pip install /path/to/tradingview_scraper
```

## Running the Server

```bash
# From project root
python -m src.tradingview_mcp.main

# Or if installed as package
tradingview-mcp
```

## Available Tools

### 1. get_historical_data
Fetch historical OHLCV data with technical indicators.

**Parameters:**
- `exchange`: Stock exchange (e.g., 'NSE', 'NASDAQ')
- `symbol`: Trading symbol (e.g., 'NIFTY', 'AAPL')
- `timeframe`: Time interval ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M')
- `numb_price_candles`: Number of candles (1-5000)
- `indicators`: List of indicators (currently supports 'RSI')

### 2. get_news_headlines
Scrape latest news headlines for a symbol.

**Parameters:**
- `symbol`: Trading symbol (required)
- `exchange`: Optional exchange filter
- `provider`: News provider or 'all'
- `area`: Geographical area filter

### 3. get_news_content
Fetch full news article content.

**Parameters:**
- `story_paths`: List of story paths from headlines

## Configuration

Set your TradingView cookies in `.env`:
```bash
# Required: Your TradingView session cookies
TRADINGVIEW_COOKIE="your_cookies_here"

# Optional: TradingView configuration (defaults will be used if not set)
TRADINGVIEW_URL="https://in.tradingview.com/chart/0M7cMdwj/?symbol=NSE%3ANIFTY"
TRADINGVIEW_HOST="in.tradingview.com"
TRADINGVIEW_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
```

### How to get your TradingView cookies:
1. Open TradingView in your browser and log in
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Refresh the page
5. Click on any request to tradingview.com
6. Copy the entire Cookie header value

**Note:** The server will automatically generate fresh JWT tokens from your cookies as needed. Tokens are cached and reused until they expire, ensuring optimal performance.

## Error Handling

All functions include comprehensive validation and return structured error messages with helpful information for debugging.

## Development

```bash
# Install in development mode
uv pip install -e .

# Run tests (if available)
uv run pytest