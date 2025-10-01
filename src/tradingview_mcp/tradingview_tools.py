"""
TradingView tools implementation for MCP server.
"""

import json
from typing import List, Dict, Optional, Any
from tradingview_scraper.symbols.stream import Streamer
from tradingview_scraper.symbols.news import NewsScraper
from tradingview_scraper.symbols.technicals import Indicators
from tradingview_scraper.symbols.ideas import Ideas
from tradingview_screener import Query, col
import pandas as pd
import os

from .validators import (
    validate_exchange, validate_timeframe, validate_news_provider,
    validate_area, validate_indicators, validate_symbol, validate_story_paths,
    ValidationError
)
from .utils import (
    merge_ohlc_with_indicators, clean_for_json,
    extract_news_body, convert_timestamp_to_indian_time
)


def fetch_historical_data(
    exchange: str,
    symbol: str,
    timeframe: str,
    numb_price_candles: int,
    indicators: List[str]
) -> Dict[str, Any]:
    """
    Fetch historical data from TradingView with indicators.
    
    Note: Free TradingView accounts are limited to maximum 2 indicators per request.
    
    Args:
        exchange: Stock exchange name
        symbol: Trading symbol
        timeframe: Time interval for candles
        numb_price_candles: Number of candles to fetch
        indicators: List of technical indicators (max 2 for free accounts)
        
    Returns:
        Dictionary with merged data and any errors
        
    Raises:
        ValidationError: If validation fails
        Exception: If data fetching fails
    """
    # Validate inputs
    exchange = validate_exchange(exchange)
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)
    
    if numb_price_candles < 1 or numb_price_candles > 5000:
        raise ValidationError(
            f"Number of candles must be between 1 and 5000. Got: {numb_price_candles}"
        )
    
    indicator_ids, indicator_versions, errors = validate_indicators(indicators)
    
    # Check for validation errors
    if errors:
        return {
            'success': False,
            'data': [],
            'errors': errors,
            'message': f"Validation failed: {'; '.join(errors)}"
        }

    try:
        streamer = Streamer(
            export_result=True,
            export_type='json',
            websocket_jwt_token=os.getenv("TRADINGVIEW_JWT_TOKEN")
        )
        
        # Fetch data from TradingView
        data = streamer.stream(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            numb_price_candles=numb_price_candles,
            indicator_id=indicator_ids,
            indicator_version=indicator_versions
        )
        
        # Convert timestamps to IST
        if 'ohlc' in data and data['ohlc']:
            for entry in data['ohlc']:
                if 'timestamp' in entry:
                    entry['datetime_ist'] = convert_timestamp_to_indian_time(entry['timestamp'])
        
        if 'indicator' in data and data['indicator']:
            for indicator_name, indicator_data in data['indicator'].items():
                for entry in indicator_data:
                    if 'timestamp' in entry:
                        entry['datetime_ist'] = convert_timestamp_to_indian_time(entry['timestamp'])
        
        # Merge OHLC with indicators if available
        merged_data = merge_ohlc_with_indicators(data)
        
        return {
            'success': True,
            'data': merged_data,
            'errors': errors,
            'metadata': {
                'exchange': exchange,
                'symbol': symbol,
                'timeframe': timeframe,
                'candles_count': len(merged_data),
                'indicators': indicators
            }
        }
        
    except ValueError as e:
        return {
            'success': False,
            'data': [],
            'errors': errors + [str(e)],
            'message': f"Data processing error: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'errors': errors + [f"TradingView API error: {str(e)}"],
            'message': f"Failed to fetch data from TradingView: {str(e)}"
        }


def fetch_news_headlines(
    symbol: str,
    exchange: Optional[str] = None,
    provider: str = "all",
    area: str = 'asia'
) -> List[Dict[str, Any]]:
    """
    Fetch news headlines from TradingView.
    
    Args:
        symbol: Trading symbol
        exchange: Optional exchange name
        provider: News provider or 'all'
        area: Geographical area
        
    Returns:
        List of news headlines
        
    Raises:
        ValidationError: If validation fails
        Exception: If fetching fails
    """
    # Validate inputs
    symbol = validate_symbol(symbol)
    exchange = validate_exchange(exchange) if exchange else None
    provider_param = validate_news_provider(provider)
    area = validate_area(area)
    
    try:
        news_scraper = NewsScraper(export_result=True, export_type='json')
        
        # Retrieve news headlines
        news_headlines = news_scraper.scrape_headlines(
            symbol=symbol,
            exchange=exchange,
            provider=provider_param,  # None for 'all'
            area=area,
            section="all",
            sort='latest'
        )
        
        # Clean and format headlines
        cleared_headlines = []
        for headline in news_headlines:
            cleared_headline = {
                "title": headline.get("title"),
                "provider": headline.get("provider"),
                "published": headline.get("published"),
                "source": headline.get("source"),
                "storyPath": headline.get("storyPath")
            }
            cleared_headlines.append(cleared_headline)
        
        return cleared_headlines
        
    except Exception as e:
        raise Exception(
            f"Failed to fetch news headlines from TradingView: {str(e)}. "
            f"Please verify symbol '{symbol}' and exchange '{exchange}' are valid."
        )


def fetch_news_content(story_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch detailed news content using story paths.
    
    Args:
        story_paths: List of story paths from news headlines
        
    Returns:
        List of news articles with content
        
    Raises:
        ValidationError: If validation fails
    """
    # Validate story paths
    story_paths = validate_story_paths(story_paths)
    
    news_scraper = NewsScraper(export_result=True, export_type='json')
    news_content = []
    
    for story_path in story_paths:
        try:
            content = news_scraper.scrape_news_content(story_path=story_path)
            
            # Clean content for JSON serialization
            cleaned_content = clean_for_json(content)
            
            # Extract text body
            body = extract_news_body(cleaned_content)
            
            news_content.append({
                "success": True,
                "title": cleaned_content.get("title", ""),
                "body": body,
                "story_path": story_path
            })
            
        except Exception as e:
            news_content.append({
                "success": False,
                "title": "",
                "body": "",
                "story_path": story_path,
                "error": f"Failed to fetch content: {str(e)}"
            })
    
    return news_content


def fetch_all_indicators(
    exchange: str,
    symbol: str,
    timeframe: str
) -> Dict[str, Any]:
    """
    Retrieve current values for all available technical indicators from TradingView.

    This function uses the `Indicators` scraper to request the full set of
    indicator values for the given symbol / exchange / timeframe. It returns
    a normalized dictionary with a boolean `success` flag and the raw
    `data` payload (only the current indicator snapshot).

    Args:
        exchange: Stock exchange name (e.g., 'NSE', 'NASDAQ'). Will be validated.
        symbol: Trading symbol (e.g., 'NIFTY', 'AAPL'). Required.
        timeframe: Timeframe string (one of VALID_TIMEFRAMES).

    Returns:
        A dict with keys:
        - success: bool
        - data: dict of indicator current values (if successful)
        - message: error message when success is False

    Raises:
        ValidationError: If validation fails for any parameter
    """
    # Validate inputs
    exchange = validate_exchange(exchange)
    symbol = validate_symbol(symbol)
    timeframe = validate_timeframe(timeframe)

    try:
        indicators_scraper = Indicators(
            export_result=True,
            export_type='json'
        )

        # Request all indicators (current snapshot)
        raw = indicators_scraper.scrape(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            allIndicators=True
        )

        # The scraper typically returns a dict with 'status' and 'data'.
        if isinstance(raw, dict) and raw.get('status') in ('success', True):
            return {
                'success': True,
                'data': raw.get('data', {})
            }

        # Fallback: return raw payload if format unexpected
        return {
            'success': False,
            'message': f'Unexpected response from Indicators scraper: {type(raw)}',
            'raw': raw
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to fetch indicators: {str(e)}'
        }


def fetch_trading_analysis(
    symbol: str,
    exchange: str,
    market: str = "america"
) -> Dict[str, Any]:
    """
    Fetch comprehensive trading analysis data for a given stock symbol.
    
    This function provides a rich set of data points covering fundamental health,
    technical signals, and overall market sentiment. It returns financial metrics,
    performance data, volatility indicators, and analyst recommendations.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'NIFTY')
        exchange: Exchange name (e.g., 'NASDAQ', 'NSE')
        market: Market region ('america', 'india', 'crypto', etc.)
        
    Returns:
        Dictionary with:
        - success: bool indicating if the operation succeeded
        - data: dict containing comprehensive analysis data when successful
        - message: error message when unsuccessful
        - metadata: information about the request
    
    Raises:
        ValidationError: If validation fails for any parameter
    """
    # Validate inputs
    symbol = validate_symbol(symbol)
    exchange = validate_exchange(exchange) if exchange else None
    
    # Validate market
    valid_markets = ['america', 'india', 'crypto', 'forex', 'bond', 'futures']
    if market.lower() not in valid_markets:
        raise ValidationError(
            f"Invalid market '{market}'. Must be one of: {', '.join(valid_markets)}"
        )
    
    try:
        # Construct query for the specific market
        query = Query().set_markets(market.lower())
        
        # Select only basic universally supported fields
        query.select(
            # Basic Identity
            'name', 'description', 'close',
            
            # Core Price & Volume
            'open', 'high', 'low', 'volume', 'change', 'change_abs',
            
            # Performance
            'Perf.W', 'Perf.1M', 'Perf.3M', 'Perf.6M', 'Perf.YTD', 'Perf.Y',
            
            # Technical Indicators (from indicators feature)
            'RSI', 'RSI[1]', 'Stoch.K', 'Stoch.D', 'CCI20', 'ADX', 'MACD.macd',
            'MACD.signal', 'Mom', 'AO', 'UO', 'W.R', 'BBPower',
            'Ichimoku.BLine', 'VWMA', 'HullMA9',
            
            # Moving Averages
            'SMA10', 'SMA20', 'SMA50', 'SMA100', 'SMA200',
            'EMA10', 'EMA20', 'EMA50', 'EMA100', 'EMA200',
            
            # Recommendations
            'Recommend.All', 'Recommend.MA', 'Recommend.Other',
        )
        
        # Set specific ticker instead of filtering (more reliable)
        if exchange:
            ticker = f"{exchange}:{symbol}"
            query.set_tickers(ticker)
        
        # Fetch the data
        try:
            count, df = query.get_scanner_data()
        except Exception as e:
            return {
                'success': False,
                'message': f'Scanner query failed: {str(e)}',
                'data': {},
                'metadata': {
                    'symbol': symbol,
                    'exchange': exchange,
                    'market': market,
                    'error_type': type(e).__name__
                }
            }
        
        # Handle empty data
        df_is_empty = False
        try:
            if hasattr(df, 'empty'):  # pandas DataFrame
                df_is_empty = df.empty
            elif hasattr(df, '__len__'):  # list or similar
                df_is_empty = len(df) == 0
            else:
                df_is_empty = not df
        except:
            df_is_empty = not df
            
        if df_is_empty:
            return {
                'success': False,
                'message': f"No data found for symbol '{symbol}' on exchange '{exchange}' in market '{market}'. Please verify the symbol and exchange are correct.",
                'data': {},
                'metadata': {
                    'symbol': symbol,
                    'exchange': exchange,
                    'market': market,
                    'total_count': count,
                    'dataframe_empty': True
                }
            }

        # Convert to dictionary format for better JSON serialization
        result_data = {}
        try:
            # Handle pandas DataFrame
            if hasattr(df, 'iloc') and hasattr(df, 'columns'):  # DataFrame
                if len(df) > 0:
                    # Get first row as dictionary
                    first_row = df.iloc[0]
                    result_data = first_row.to_dict()
            # Handle other data structures
            elif hasattr(df, '__len__') and len(df) > 0:
                if hasattr(df, 'columns'):  # Has column info
                    result_data = dict(zip(df.columns, df.iloc[0] if hasattr(df, 'iloc') else df[0]))
                else:
                    # Fallback - just return what we got
                    result_data = {'raw_data': df}
        except Exception as e:
            # Fallback: return error with debug info
            return {
                'success': False,
                'message': f'Data processing error: {str(e)}',
                'data': {},
                'debug_info': {
                    'data_type': str(type(df)),
                    'data_str': str(df)[:200] if df is not None else 'None',
                    'count': count,
                    'has_columns': hasattr(df, 'columns'),
                    'has_iloc': hasattr(df, 'iloc'),
                }
            }        # Clean and organize the data safely
        def safe_get(data_dict, key, default=None):
            """Safely get value from dict, handling any data type"""
            try:
                return data_dict.get(key, default)
            except:
                return default
        
        organized_data = {
            'basic_info': {
                'name': safe_get(result_data, 'name'),
                'description': safe_get(result_data, 'description'),
                'type': safe_get(result_data, 'type'),
                'exchange': exchange,
                'market': market,
            },
            'price_volume': {
                'close': safe_get(result_data, 'close'),
                'open': safe_get(result_data, 'open'),
                'high': safe_get(result_data, 'high'),
                'low': safe_get(result_data, 'low'),
                'volume': safe_get(result_data, 'volume'),
            },
            'performance': {
                'change': safe_get(result_data, 'change'),
                'change_abs': safe_get(result_data, 'change_abs'),
                'week_performance': safe_get(result_data, 'Perf.W'),
                'month_1_performance': safe_get(result_data, 'Perf.1M'),
                'month_3_performance': safe_get(result_data, 'Perf.3M'),
                'month_6_performance': safe_get(result_data, 'Perf.6M'),
                'ytd_performance': safe_get(result_data, 'Perf.YTD'),
                'year_performance': safe_get(result_data, 'Perf.Y'),
            },
            'technical_indicators': {
                'rsi': safe_get(result_data, 'RSI'),
                'rsi_previous': safe_get(result_data, 'RSI[1]'),
                'stoch_k': safe_get(result_data, 'Stoch.K'),
                'stoch_d': safe_get(result_data, 'Stoch.D'),
                'cci': safe_get(result_data, 'CCI20'),
                'adx': safe_get(result_data, 'ADX'),
                'macd': safe_get(result_data, 'MACD.macd'),
                'macd_signal': safe_get(result_data, 'MACD.signal'),
                'momentum': safe_get(result_data, 'Mom'),
                'awesome_oscillator': safe_get(result_data, 'AO'),
                'ultimate_oscillator': safe_get(result_data, 'UO'),
                'williams_r': safe_get(result_data, 'W.R'),
                'bb_power': safe_get(result_data, 'BBPower'),
                'ichimoku_base': safe_get(result_data, 'Ichimoku.BLine'),
                'vwma': safe_get(result_data, 'VWMA'),
                'hull_ma': safe_get(result_data, 'HullMA9'),
            },
            'moving_averages': {
                'sma_10': safe_get(result_data, 'SMA10'),
                'sma_20': safe_get(result_data, 'SMA20'),
                'sma_50': safe_get(result_data, 'SMA50'),
                'sma_100': safe_get(result_data, 'SMA100'),
                'sma_200': safe_get(result_data, 'SMA200'),
                'ema_10': safe_get(result_data, 'EMA10'),
                'ema_20': safe_get(result_data, 'EMA20'),
                'ema_50': safe_get(result_data, 'EMA50'),
                'ema_100': safe_get(result_data, 'EMA100'),
                'ema_200': safe_get(result_data, 'EMA200'),
            },
            'recommendations': {
                'overall_recommendation': safe_get(result_data, 'Recommend.All'),
                'ma_recommendation': safe_get(result_data, 'Recommend.MA'),
                'other_recommendation': safe_get(result_data, 'Recommend.Other'),
            },
        }
        
        return {
            'success': True,
            'data': organized_data,
            'metadata': {
                'symbol': symbol,
                'exchange': exchange,
                'market': market,
                'fields_count': len([v for v in result_data.values() if v is not None]),
                'total_count': count,
                'df_columns': list(df.columns) if hasattr(df, 'columns') else []
            }
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Failed to fetch trading analysis: {str(e)}',
            'data': {},
            'metadata': {
                'symbol': symbol,
                'exchange': exchange,
                'market': market,
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
        }


def fetch_ideas(
    symbol: str,
    startPage: int = 1,
    endPage: int = 1,
    sort: str = 'popular',
    export_result: bool = True,
    export_type: str = 'json'
) -> Dict[str, Any]:
    """
    Fetch trading ideas for a given symbol using the Ideas scraper.

    Args:
        symbol: Trading symbol/ticker
        startPage: Starting page number (>=1)
        endPage: Ending page number (>= startPage)
        sort: 'popular' or 'recent'
        export_result: Whether to export results (passed to Ideas)
        export_type: Export format for Ideas

    Returns:
        Dict with keys: success (bool), ideas (list), count (int), message (str)

    Raises:
        ValidationError: For invalid inputs
    """
    # Validate inputs
    symbol = validate_symbol(symbol)

    if endPage < startPage:
        raise ValidationError("endPage must be greater than or equal to startPage.")

    if sort not in ('popular', 'recent'):
        raise ValidationError("sort must be either 'popular' or 'recent'.")

    try:
        ideas_scraper = Ideas(
            export_result=export_result,
            export_type=export_type
        )

        ideas = ideas_scraper.scrape(
            symbol=symbol,
            startPage=startPage,
            endPage=endPage,
            sort=sort
        )

        return {
            'success': True,
            'ideas': ideas,
            'count': len(ideas) if ideas is not None else 0,
            'message': f"Scraped {len(ideas) if ideas is not None else 0} ideas for symbol '{symbol}'"
        }

    except ValidationError:
        # Re-raise validation errors so callers can handle them consistently
        raise
    except Exception as e:
        return {
            'success': False,
            'ideas': [],
            'count': 0,
            'message': f'Failed to fetch ideas: {str(e)}'
        }