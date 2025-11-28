# TradingView MCP Server

A FastMCP server that provides tools to scrape and fetch real-time data from TradingView, including historical prices, technical indicators, news, trading ideas, and options chain analysis.

## Installation

### Install with pip
```bash
git clone https://github.com/smitkunpara/tradingview-mcp.git
cd tradingview-mcp
pip install -e .
cp .env.example .env  # Copy and edit with your TradingView cookies
```

### Install with uv (recommended)
```bash
git clone https://github.com/smitkunpara/tradingview-mcp.git
cd tradingview-mcp
uv sync
cp .env.example .env  # Copy and edit with your TradingView cookies
```

## Configuration

### Getting TradingView Cookies
1. Visit [TradingView](https://www.tradingview.com/) and log in to your account
2. Open any chart (e.g., NIFTY, Bitcoin, or any symbol)
3. Open Developer Tools (F12) and go to the **Network** tab
4. Reload the page (F5 or Ctrl+R)
5. Look for a **GET** request with URL: `https://in.tradingview.com/chart/?symbol=<symbol_id>` (where `<symbol_id>` is something like `NSE%3ANIFTY` or `BINANCE%3ABTCUSDT`)
6. Click on that request to open it
7. Go to the **Request Headers** section
8. Find the `Cookie` header and copy its entire value 
9. **Important:** .env files require proper escaping of quotes within values. If your cookie contains quotes, they must be escaped as `\"` for the .env parser to work correctly.
10. Paste this value into your `.env` file as `TRADINGVIEW_COOKIE="your_cookies_here"`

### String Escaper Tool

Since there's no official built-in way to escape cookie strings for .env files, here's a simple Python script you can use to properly escape your TradingView cookies:

```python
# Save this as escape_cookie.py and run: python escape_cookie.py
import json

# Paste your raw cookie string here (without quotes)
raw_cookie = input("Paste your cookie string: ")

# Escape the quotes for .env file
escaped_cookie = raw_cookie.replace('"', '\\"')

# Output the properly escaped string
print(f'\\nEscaped cookie for .env file:')
print(f'TRADINGVIEW_COOKIE="{escaped_cookie}"')
```

**Usage:**
1. Copy the script above and save it as `escape_cookie.py`
2. Run `python escape_cookie.py`
3. Paste your raw cookie string when prompted
4. Copy the escaped output to your `.env file`

**Alternative:** You can also use online JSON escape tools or text editors with find/replace functionality to replace `"` with `\"`.

### MCP Configuration

To use this server with an MCP client (like Claude Desktop), add the following configuration to your MCP settings file (usually `mcp.json` or similar):

```json
{
  "servers": {
    "TradingView": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "src.tradingview_mcp.main"
      ],
      "env": {
        "TRADINGVIEW_COOKIE": "your_tradingview_cookies_here",
        "TRADINGVIEW_URL": "https://in.tradingview.com/chart/your_chart_id/?symbol=NSE%3ANIFTY",
        "TRADINGVIEW_HOST": "in.tradingview.com",
        "TRADINGVIEW_USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
      }
    }
  }
}
```

**Note:** Replace the placeholder values with your actual TradingView data:
- `"your_tradingview_cookies_here"`: Your escaped TradingView cookies
- `"your_chart_id"`: Your actual TradingView chart ID (obtained from the Configuration section above)
- Other values can usually use the defaults shown

## Usage

The server provides MCP tools that can be called programmatically. Here are the available tools:

### 1. get_historical_data
Fetch historical OHLCV (Open, High, Low, Close, Volume) data with technical indicators.

**Example:**
```python
# Get last 100 1-minute candles for NIFTY with RSI
result = get_historical_data(
    exchange="NSE",
    symbol="NIFTY",
    timeframe="1m",
    numb_price_candles=100,
    indicators=["RSI"]
)
```

### 2. get_news_headlines
Get latest news headlines for a trading symbol.

**Example:**
```python
# Get news for NIFTY from NSE
headlines = get_news_headlines(
    symbol="NIFTY",
    exchange="NSE",
    provider="all",
    area="asia"
)
```

### 3. get_news_content
Fetch full content of news articles using story paths from headlines.

**Example:**
```python
# Get full content for specific articles
articles = get_news_content(story_paths=["/news/story1", "/news/story2"])
```

### 4. get_all_indicators
Get current values for all available technical indicators for a symbol.

**Example:**
```python
# Get all indicators for NIFTY on 1-minute timeframe
indicators = get_all_indicators(
    symbol="NIFTY",
    exchange="NSE",
    timeframe="1m"
)
```

### 5. get_ideas
Scrape trading ideas from the TradingView community.

**Example:**
```python
# Get popular ideas for NIFTY (pages 1-2)
ideas = get_ideas(
    symbol="NIFTY",
    startPage=1,
    endPage=2,
    sort="popular"
)
```

### 6. get_option_chain_greeks
Get detailed options chain with full Greeks, implied volatility, and analytics.

**Example:**
```python
# Get latest expiry options for NIFTY with 5 strikes per side
options = get_option_chain_greeks(
    symbol="NIFTY",
    exchange="NSE",
    expiry_date="latest",
    top_n=5
)
```

## Contributing

This project is open source and welcomes contributions from the community! Whether you're fixing bugs, adding new features, improving documentation, or sharing ideas, your input is valuable.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Submit a pull request with a clear description of your changes

### Development Setup

```bash
# Clone and setup
git clone https://github.com/smitkunpara/tradingview-mcp.git
cd tradingview-mcp
uv sync

# Run the server for development
python -m src.tradingview_mcp.main
```

We appreciate all contributions, big or small! Please feel free to open issues for bugs, feature requests, or general discussions.

## License

> **⚠️ Note:** This repository contains AI-generated code. While efforts have been made to ensure quality and security, please review the code before using in production environments.

[Add your license here]

## Support

For issues or questions, please open an issue on GitHub.