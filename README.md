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

set your TradingView JWT token in `.env`:
```
TRADINGVIEW_JWT_TOKEN=your_token_here
```

## Error Handling

All functions include comprehensive validation and return structured error messages with helpful information for debugging.

## Development

```bash
# Install in development mode
uv pip install -e .

# Run tests (if available)
uv run pytest