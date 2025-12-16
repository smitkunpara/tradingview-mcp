"""
Pydantic models for TradingView HTTP API requests.
These models define the request/response schemas for all API endpoints.
"""

import sys
import os
from typing import List, Optional, Literal, Union
from pydantic import Field, BaseModel

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.tradingview_mcp.validators import (
    VALID_EXCHANGES, VALID_TIMEFRAMES, VALID_NEWS_PROVIDERS,
    VALID_AREAS, INDICATOR_MAPPING
)


class HistoricalDataRequest(BaseModel):
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE', 'NASDAQ', 'BINANCE'). Must be one of the valid exchanges like {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field(..., description="Time interval for each candle. Options: 1m (1 minute), 5m, 15m, 30m, 1h (1 hour), 2h, 4h, 1d (1 day), 1w (1 week), 1M (1 month)")
    numb_price_candles: Union[int, str] = Field(..., description="Number of historical candles to fetch (1-5000). Accepts int or str (e.g., 100 or '100'). More candles = longer history. E.g., 100 for last 100 periods.")
    indicators: List[str] = Field(default=[], description=f"List of technical indicators to include. Options: {', '.join(INDICATOR_MAPPING.keys())}. Example: ['RSI', 'MACD', 'CCI', 'BB']. Leave empty for no indicators.")


class NewsHeadlinesRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol for news (e.g., 'NIFTY', 'AAPL', 'BTC'). Required. Search online for correct symbol.")
    exchange: Optional[str] = Field(None, min_length=2, max_length=30, description=f"Optional exchange filter. One of: {', '.join(VALID_EXCHANGES)}... Leave empty for all exchanges.")
    provider: str = Field("all", min_length=3, max_length=20, description=f"News provider filter. Options: {', '.join(VALID_NEWS_PROVIDERS)}... or 'all' for all providers.")
    area: Literal['world', 'americas', 'europe', 'asia', 'oceania', 'africa'] = Field('asia', description="Geographical area filter for news. Default is 'asia'.")


class NewsContentRequest(BaseModel):
    story_paths: List[str] = Field(..., min_length=1, max_length=20, description="List of story paths from news headlines. Each path must start with '/news/'. Get these from get_news_headlines() results.")


class AllIndicatorsRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Required.")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    timeframe: Literal['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w', '1M'] = Field('1m', description=f"Time interval for indicator snapshot. Valid options: {', '.join(VALID_TIMEFRAMES)}")


class IdeasRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Search online for correct symbol format for your exchange.")
    startPage: Union[int, str] = Field(1, description="Starting page number for scraping ideas. Accepts int or str (e.g., 1 or '1').")
    endPage: Union[int, str] = Field(1, description="Ending page number for scraping ideas. Accepts int or str (e.g., 1 or '1').")
    sort: Literal['popular', 'recent'] = Field('popular', description="Sorting order for ideas. 'popular' for most liked, 'recent' for latest.")


class MindsRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol/ticker (e.g., 'NIFTY', 'AAPL', 'BTCUSD'). Required.")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    limit: Optional[Union[int, str]] = Field(None, description="Maximum number of discussions to retrieve from first page. If None, fetches all available. Accepts int or str (e.g., 100 or '100').")


class OptionChainGreeksRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20, description="Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY'). Required.")
    exchange: str = Field(..., min_length=2, max_length=30, description=f"Stock exchange name (e.g., 'NSE'). Must be one of the valid exchanges. Valid examples: {', '.join(VALID_EXCHANGES[:5])}... Use uppercase format.")
    expiry_date: Optional[Union[int, str]] = Field('nearest', description="Option expiry date:\n- 'nearest' (default): NEAREST expiry only\n- 'all': ALL expiries grouped by date\n- int YYYYMMDD (e.g., 20251202): SPECIFIC expiry")
    no_of_ITM: Union[int, str] = Field(5, description="Number of In-The-Money strikes. Default 5, max 20.")
    no_of_OTM: Union[int, str] = Field(5, description="Number of Out-of-The-Money strikes. Default 5, max 20.")