# TradingView MCP Server

A FastMCP server that provides tools to scrape and fetch real-time data from TradingView, including historical prices, technical indicators, news, trading ideas, and options chain analysis.

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
        "TRADINGVIEW_URL": "https://www.tradingview.com/chart/your_chart_id/?symbol=BINANCE%3ABTCUSDT",
        // optional settings
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

## Available MCP Tools

The server provides the following MCP tools:

- **get_historical_data**: Fetch historical OHLCV data with technical indicators
- **get_news_headlines**: Get latest news headlines for trading symbols
- **get_news_content**: Fetch full content of news articles
- **get_all_indicators**: Get current values for all technical indicators
- **get_ideas**: Scrape trading ideas from TradingView community
- **get_option_chain_greeks**: Get detailed options chain with Greeks and analytics

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
