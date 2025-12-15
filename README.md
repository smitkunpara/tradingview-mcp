# TradingView MCP Server

A FastMCP server and HTTP API that provides tools to scrape and fetch real-time data from TradingView, including historical prices, technical indicators, news, trading ideas, and options chain analysis. Supports both MCP protocol for AI assistants and REST API for direct integration.

## Installation

### Install with uv (recommended)
```bash
git clone https://github.com/smitkunpara/tradingview-mcp.git
cd tradingview-mcp
uv sync
cp .env.example .env  # Copy and edit with your TradingView cookies
```

### Install with pip
```bash
git clone https://github.com/smitkunpara/tradingview-mcp.git
cd tradingview-mcp
pip install -e .
cp .env.example .env  # Copy and edit with your TradingView cookies
```

## MCP Server Setup

To use the server with MCP-compatible clients (e.g., VS Code with MCP extension):

1. Create `.vscode/mcp.json` in your workspace root.
2. Add the following configuration (replace with your values):

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
      }
    }
  }
}
```

This sets up the stdio server for MCP integration.

## Configuration

### Getting TradingView Cookies
1. Visit [TradingView](https://www.tradingview.com/) and log in to your account
2. Open any chart (e.g., NASDAQ, Bitcoin, or any symbol)
3. Open Developer Tools (F12) and go to the **Network** tab
4. Reload the page (F5 or Ctrl+R)
5. Look for a **GET** request with URL: `https://www.tradingview.com/chart/?symbol=<symbol_id>` (where `<symbol_id>` is something like `BINANCE%3ABTCUSDT`)
6. Click on that request to open it
7. Go to the **Request Headers** section
8. Find the `Cookie` header and copy its entire value 
9. **Important:** .env files require proper escaping of quotes within values. If your cookie contains quotes, they must be escaped as `\"` for the .env parser to work correctly.
10. Paste this value into your `.env` file as `TRADINGVIEW_COOKIE="your_cookies_here"`

**Note:** Convert the cookies to [escaped format](https://onlinestringtools.com/escape-string) 

## HTTP API Server

The project also includes a FastAPI-based HTTP server that provides the same functionality as REST API endpoints. This is useful for direct HTTP requests or integration with web applications.

### Running the HTTP Server

```bash
# Using uv (recommended)
uv run python src/tradingview_mcp/http_main.py

# Or using python directly
python src/tradingview_mcp/http_main.py
```

The server will start on `http://localhost:8000` with automatic API documentation at `http://localhost:8000/docs`.

**Note:** The HTTP server uses the same environment variables as the MCP server. Make sure your `.env` file contains the `TRADINGVIEW_COOKIE` variable.

### Example HTTP Request

```bash
curl -X POST "http://localhost:8000/historical-data" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "NSE",
    "symbol": "NIFTY",
    "timeframe": "1d",
    "numb_price_candles": 100,
    "indicators": ["RSI", "MACD"]
  }'
```

## Available Tools/Endpoints

The server provides the following functionality through both MCP tools and HTTP API endpoints:

### Data Fetching Tools
- **get_historical_data / POST /historical-data**: Fetch historical OHLCV data with technical indicators
  - Supports multiple exchanges (NSE, NASDAQ, BINANCE, etc.)
  - Timeframes: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M
  - Indicators: RSI, MACD, CCI, Bollinger Bands, and more
  - Returns TOON-encoded data for token efficiency

- **get_all_indicators / POST /all-indicators**: Get current values for all technical indicators
  - Real-time indicator snapshots
  - Supports all major technical indicators

### News & Content Tools
- **get_news_headlines / POST /news-headlines**: Get latest news headlines for trading symbols
  - Filter by exchange, provider, and geographical area
  - Supports multiple news sources

- **get_news_content / POST /news-content**: Fetch full content of news articles
  - Extract complete article text from story paths
  - Handles multiple articles in single request

### Community & Analysis Tools
- **get_ideas / POST /ideas**: Scrape trading ideas from TradingView community
  - Sort by popularity or recency
  - Paginated results

- **get_minds / POST /minds**: Get community discussions from TradingView Minds
  - Fetches discussions, questions, and sentiment
  - Returns structured data with author, text, likes, and comments
  - Supports filtering by symbol and exchange

- **get_option_chain_greeks / POST /option-chain-greeks**: Get detailed options chain with Greeks and analytics
  - Complete Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
  - Implied Volatility analysis
  - Bid/ask spreads and theoretical pricing
  - Supports multiple expiries and strike filtering

### Additional Endpoints
- **GET /privacy-policy**: View privacy policy and disclaimer
- **GET /openapi.json**: OpenAPI specification for the API (auto-generated by FastAPI)
- **GET /**: API information and available endpoints

All endpoints return structured JSON responses with TOON encoding for efficient token usage in AI applications.

## Extension Configuration

For Chrome extension installation and usage instructions, see [cookie_updater_extension/README.md](cookie_updater_extension/README.md).

## Vercel Deployment & ChatGPT Integration

Deploy to Vercel to expose the FastAPI endpoints. Connect ChatGPT or a custom GPT by calling the endpoints with `X-Client-Key`.

- **Entrypoint**: `vercel/index.py`
- **Env vars**: `TRADINGVIEW_COOKIE`, `VERCEL_URL`, `TV_ADMIN_KEY`, `TV_CLIENT_KEY`
- **Headers**: `X-Admin-Key` (admin), `X-Client-Key` (client)

OpenAPI & Privacy Policy
- Import spec: `<your-vercel-url>/openapi.json`
- Privacy policy: `<your-vercel-url>/privacy-policy`
- `servers[0].url` updates to the latest deployment URL; re-import if needed.

Update-cookies endpoint
- Endpoint: `POST /update-cookies` (requires `X-Admin-Key`)
- Example:
  ```bash
  curl -X POST "https://your-app.vercel.app/update-cookies" \
    -H "Content-Type: application/json" \
    -H "X-Admin-Key: <your-admin-key>" \
    -d '{"cookies": [{"name": "sessionid", "value": "..."}], "source": "extension"}'
  ```
- No redeploy needed; server updates cookies at runtime.


## Contributing

This project is open source and welcomes contributions from the community! Whether you're fixing bugs, adding new features, improving documentation, or sharing ideas, your input is valuable.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Submit a pull request with a clear description of your changes


We appreciate all contributions, big or small! Please feel free to open issues for bugs, feature requests, or general discussions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
