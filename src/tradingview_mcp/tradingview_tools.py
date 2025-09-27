"""
TradingView tools implementation for MCP server.
"""

import json
from typing import List, Dict, Optional, Any
from tradingview_scraper.symbols.stream import Streamer
from tradingview_scraper.symbols.news import NewsScraper
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
    
    Args:
        exchange: Stock exchange name
        symbol: Trading symbol
        timeframe: Time interval for candles
        numb_price_candles: Number of candles to fetch
        indicators: List of technical indicators
        
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