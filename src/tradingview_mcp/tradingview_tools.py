"""
TradingView tools implementation for MCP server.
"""

import json
from typing import List, Dict, Optional, Any, Tuple
from tradingview_scraper.symbols.stream import Streamer
from tradingview_scraper.symbols.news import NewsScraper
from tradingview_scraper.symbols.technicals import Indicators
from tradingview_scraper.symbols.ideas import Ideas
import jwt
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
import io

from .validators import (
    validate_exchange, validate_timeframe, validate_news_provider,
    validate_area, validate_indicators, validate_symbol, validate_story_paths,
    ValidationError
)
from .utils import (
    merge_ohlc_with_indicators, clean_for_json,
    extract_news_body, convert_timestamp_to_indian_time
)
from .auth import extract_jwt_token, get_token_info


# Global token cache with thread lock
_token_cache = {
    'token': None,
    'expiry': 0
}
_token_lock = threading.Lock()


def get_valid_jwt_token(force_refresh: bool = False) -> str:
    """
    Get a valid JWT token, reusing cached token if not expired.
    
    Args:
        force_refresh: Force token refresh even if cached token is valid
        
    Returns:
        Valid JWT token string
        
    Raises:
        ValueError: If unable to generate token
    """
    global _token_cache
    
    with _token_lock:
        current_time = int(time.time())
        
        # Check if cached token is still valid (with 60 second buffer)
        if not force_refresh and _token_cache['token'] and _token_cache['expiry'] > (current_time + 60):
            return _token_cache['token']
        
        # Generate new token
        try:
            token = extract_jwt_token()
            if not token:
                raise ValueError("Failed to extract JWT token")
            
            # Get token expiry
            token_info = get_token_info(token)
            if not token_info.get('valid'):
                raise ValueError(f"Invalid token: {token_info.get('error', 'Unknown error')}")
            
            # Cache the token
            _token_cache['token'] = token
            _token_cache['expiry'] = token_info.get('exp', current_time + 3600)  # Default 1 hour if no exp
            
            return token
            
        except ValueError:
            # Re-raise with original message
            raise
        except Exception as e:
            raise ValueError(
                f"Token is not generated with cookies. Please verify your cookies. Error: {str(e)}"
            )


def is_jwt_token_valid(token: str) -> bool:
    """
    Check if the provided JWT token is valid (not expired).
    
    Args:
        token: JWT token string
    Returns:
        True if valid, False if expired
    """
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get('exp')
        current_time = int(time.time())
        return exp is not None and exp > current_time
    except Exception:
        print("Error decoding JWT token.")
        return False

def fetch_historical_data(
    exchange: str,
    symbol: str,
    timeframe: str,
    numb_price_candles: int,
    indicators: List[str]
) -> Dict[str, Any]:
    """
    Fetch historical data from TradingView with indicators using threading.
    
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
    
    # Convert string to int if necessary
    try:
        numb_price_candles = int(numb_price_candles)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Number of candles must be a valid integer or string that can be converted to integer. Got: {numb_price_candles}"
        )

    if numb_price_candles < 1 or numb_price_candles > 5000:
        raise ValidationError(
            f"Number of candles must be between 1 and 5000. Got: {numb_price_candles}"
        )
    
    indicator_ids, indicator_versions, errors, warnings = validate_indicators(indicators)

    # If there are fatal validation errors (unrecognized indicators), return
    if errors:
        return {
            'success': False,
            'data': [],
            'errors': errors,
            'message': f"Validation failed: {'; '.join(errors)}"
        }

    try:
        # Check if cookies are set
        if not os.getenv("TRADINGVIEW_COOKIE"):
            raise ValidationError(
                "Account is not connected with MCP. Please set TRADINGVIEW_COOKIE "
                "environment variable to connect your account."
            )
        
        # Get valid JWT token
        try:
            jwt_token = get_valid_jwt_token()
        except ValueError as e:
            raise ValidationError(str(e))
        
        # If no indicators requested, just fetch once
        if not indicator_ids:
            streamer = Streamer(
                export_result=True,
                export_type='json',
                websocket_jwt_token=jwt_token
            )

            # Capture stdout to prevent print statements from corrupting JSON
            with contextlib.redirect_stdout(io.StringIO()):
                data = streamer.stream(
                    exchange=exchange,
                    symbol=symbol,
                    timeframe=timeframe,
                    numb_price_candles=numb_price_candles,
                    indicator_id=[],
                    indicator_version=[]
                )
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

        # Batch indicators into groups of 2 (free account limit)
        BATCH_SIZE = 2
        batched_ids = [indicator_ids[i:i+BATCH_SIZE] for i in range(0, len(indicator_ids), BATCH_SIZE)]
        batched_versions = [indicator_versions[i:i+BATCH_SIZE] for i in range(0, len(indicator_versions), BATCH_SIZE)]

        combined_response = {'ohlc': None, 'indicator': {}}
        fetch_errors = []
        
        def fetch_batch(batch_index: int, batch_ids: List[str], batch_versions: List[int]) -> Tuple[int, Dict, Optional[str]]:
            """
            Fetch a single batch of indicators in a thread.

            Returns:
                Tuple of (batch_index, response_data, error_message)
            """
            try:
                # For subsequent batches, request one extra candle per previous batch
                extra = batch_index  # 0 for first batch, 1 for second, etc.
                fetch_candles = numb_price_candles + extra

                # Generate fresh token for this batch
                try:
                    batch_token = get_valid_jwt_token()
                except ValueError as e:
                    return (batch_index, None, f"Token generation failed: {str(e)}")

                # Create a fresh Streamer per batch
                batch_streamer = Streamer(
                    export_result=True,
                    export_type='json',
                    websocket_jwt_token=batch_token
                )

                # Capture stdout to prevent print statements from corrupting JSON
                with contextlib.redirect_stdout(io.StringIO()):
                    resp = batch_streamer.stream(
                        exchange=exchange,
                        symbol=symbol,
                        timeframe=timeframe,
                        numb_price_candles=fetch_candles,
                        indicator_id=batch_ids,
                        indicator_version=batch_versions
                    )

                return (batch_index, resp, None)

            except Exception as e:
                return (batch_index, None, f"Batch {batch_index} failed: {str(e)}")
        
        # Use ThreadPoolExecutor to fetch batches in parallel
        with ThreadPoolExecutor(max_workers=len(batched_ids)) as executor:
            # Submit all batch fetch tasks
            future_to_batch = {
                executor.submit(fetch_batch, idx, batch_ids, batch_versions): idx
                for idx, (batch_ids, batch_versions) in enumerate(zip(batched_ids, batched_versions))
            }
            
            # Collect results as they complete
            batch_results = {}
            for future in as_completed(future_to_batch):
                batch_index, resp, error = future.result()
                
                if error:
                    fetch_errors.append(error)
                    continue
                
                batch_results[batch_index] = resp

        # Process results in order
        for batch_index in sorted(batch_results.keys()):
            resp = batch_results[batch_index]
            
            # Save OHLC from the first response only
            if combined_response['ohlc'] is None:
                combined_response['ohlc'] = resp.get('ohlc', [])

            # Merge indicator arrays: append entries for each tradingview key
            for ind_key, ind_values in (resp.get('indicator') or {}).items():
                if ind_key not in combined_response['indicator']:
                    combined_response['indicator'][ind_key] = []
                # Append new values; allow duplicates — merge function will match by timestamp
                combined_response['indicator'][ind_key].extend(ind_values or [])

            # Collect any errors returned by the streamer resp
            if isinstance(resp, dict) and resp.get('errors'):
                fetch_errors.extend(resp.get('errors'))

        # Ensure we have an ohlc list
        if not combined_response.get('ohlc'):
            raise ValueError('Failed to fetch OHLC data from TradingView across batches.')

        # Do not convert timestamps here; merge_ohlc_with_indicators will handle datetime conversion
        merged_data = merge_ohlc_with_indicators(combined_response)

        # If merge appended a final entry with _merge_errors, extract them
        merge_errors = []
        if merged_data and isinstance(merged_data[-1], dict) and '_merge_errors' in merged_data[-1]:
            merge_errors = merged_data[-1].get('_merge_errors', [])
            merged_data = merged_data[:-1]

        all_errors = errors + fetch_errors + merge_errors

        return {
            'success': True,
            'data': merged_data,
            'errors': all_errors,
            'warnings': warnings,
            'metadata': {
                'exchange': exchange,
                'symbol': symbol,
                'timeframe': timeframe,
                'candles_count': len(merged_data),
                'indicators': indicators,
                'batches': len(batched_ids)
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

        # Capture stdout to prevent print statements from corrupting JSON
        with contextlib.redirect_stdout(io.StringIO()):
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
            # Capture stdout to prevent print statements from corrupting JSON
            with contextlib.redirect_stdout(io.StringIO()):
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

        # Capture stdout to prevent print statements from corrupting JSON
        with contextlib.redirect_stdout(io.StringIO()):
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

    # Convert string to int if necessary for startPage and endPage
    try:
        startPage = int(startPage)
    except (ValueError, TypeError):
        raise ValidationError(
            f"startPage must be a valid integer or string that can be converted to integer. Got: {startPage}"
        )

    try:
        endPage = int(endPage)
    except (ValueError, TypeError):
        raise ValidationError(
            f"endPage must be a valid integer or string that can be converted to integer. Got: {endPage}"
        )

    if endPage < startPage:
        raise ValidationError("endPage must be greater than or equal to startPage.")

    if sort not in ('popular', 'recent'):
        raise ValidationError("sort must be either 'popular' or 'recent'.")

    try:
        ideas_scraper = Ideas(
            export_result=export_result,
            export_type=export_type
        )

        # Capture stdout to prevent print statements from corrupting JSON
        with contextlib.redirect_stdout(io.StringIO()):
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


def fetch_option_chain_data(
    symbol: str,
    exchange: str,
    expiry_date: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fetch option chain data with Greeks and IV from TradingView.
    
    Args:
        symbol: Underlying symbol (e.g., 'NIFTY', 'BANKNIFTY')
        exchange: Exchange name (e.g., 'NSE')
        expiry_date: Optional expiry date in YYYYMMDD format. If None, fetches all expiries.
    
    Returns:
        Dictionary containing option chain data with Greeks
    """
    import requests
    
    try:
        # Request option chain data
        url = "https://scanner.tradingview.com/options/scan2?label-product=options-overlay"
        
        # Build filter - include expiry only if provided
        filter_conditions = [
            {"left": "type", "operation": "equal", "right": "option"},
            {"left": "root", "operation": "equal", "right": symbol}
        ]
        
        if expiry_date is not None:
            filter_conditions.append(
                {"left": "expiration", "operation": "equal", "right": expiry_date}
            )
        
        payload = {
            "columns": [
                "ask", "bid", "currency", "delta", "expiration", "gamma", 
                "iv", "option-type", "pricescale", "rho", "root", "strike", 
                "theoPrice", "theta", "vega", "bid_iv", "ask_iv"
            ],
            "filter": filter_conditions,
            "ignore_unknown_fields": False,
            "index_filters": [
                {"name": "underlying_symbol", "values": [f"{exchange}:{symbol}"]}
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'total_count': data.get('totalCount', 0)
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to fetch option chain: {str(e)}',
            'data': None
        }


def get_current_spot_price(symbol: str, exchange: str) -> Dict[str, Any]:
    """
    Get current spot price of underlying symbol.
    
    Args:
        symbol: Symbol name (e.g., 'NIFTY')
        exchange: Exchange name (e.g., 'NSE')
    
    Returns:
        Dictionary with spot price and pricescale
    """
    import requests
    
    try:
        url = "https://scanner.tradingview.com/global/scan2?label-product=options-overlay"
        
        payload = {
            "columns": ["close", "pricescale"],
            "ignore_unknown_fields": False,
            "symbols": {
                "tickers": [f"{exchange}:{symbol}"]
            }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('symbols') and len(data['symbols']) > 0:
            symbol_data = data['symbols'][0]
            close_price = symbol_data['f'][0]
            pricescale = symbol_data['f'][1]
            
            return {
                'success': True,
                'spot_price': close_price,
                'pricescale': pricescale
            }
        
        return {
            'success': False,
            'message': 'No price data found'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to fetch spot price: {str(e)}'
        }


def process_option_chain_with_analysis(
    symbol: str,
    exchange: str,
    expiry_date: Optional[str] = None,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Fetch and process option chain data with Greeks (Delta, Gamma, Theta, Vega, Rho), Implied Volatility (IV), 
    and detailed strike analysis for options trading.
    
    This function provides comprehensive option chain data including:
    - Current spot price of the underlying asset
    - ITM (In-The-Money) strikes: Strikes below the current spot price
    - OTM (Out-of-The-Money) strikes: Strikes at or above the current spot price
    - Complete Greeks for both Call and Put options at each strike
    - Implied Volatility (IV) data: overall IV, bid IV, and ask IV
    - Intrinsic value and time value calculations
    - Aggregate analytics: ATM strike, total deltas, net delta exposure
    
    Greeks Included:
    - Delta: Rate of change of option price with respect to underlying price
    - Gamma: Rate of change of delta with respect to underlying price
    - Theta: Rate of option price decay with respect to time
    - Vega: Sensitivity of option price to volatility changes
    - Rho: Sensitivity of option price to interest rate changes
    
    Args:
        symbol (str): Underlying symbol name (e.g., 'NIFTY', 'BANKNIFTY')
        exchange (str): Exchange where options are traded (e.g., 'NSE')
        expiry_date (str|int|None): 
            - None: Returns data grouped by ALL available expiry dates
            - "latest": Returns data for the NEAREST upcoming expiry date only
            - Integer (YYYYMMDD): Returns data for that specific expiry date (e.g., 20251202)
        top_n (int): Number of strikes to return above and below the spot price. 
                     Default is 5. Each direction (ITM/OTM) will have top_n strikes.
    
    Returns:
        Dict[str, Any]: Structured dictionary containing:
        
        For specific expiry (when expiry_date is an integer or "latest"):
        {
            'success': True,
            'spot_price': float,  # Current spot price of underlying
            'expiry': int,  # Expiry date in YYYYMMDD format
            'itm_strikes': [  # Strikes below spot (In-The-Money for Calls)
                {
                    'strike': float,
                    'call': {
                        'symbol': str,  # TradingView symbol (e.g., 'NSE:NIFTY251202C25700')
                        'ask': float, 'bid': float,
                        'delta': float, 'gamma': float, 'theta': float, 'vega': float, 'rho': float,
                        'iv': float,  # Implied Volatility (overall)
                        'bid_iv': float, 'ask_iv': float,  # Bid/Ask IV
                        'theo_price': float,  # Theoretical option price
                        'intrinsic_value': float, 'time_value': float
                    },
                    'put': { ... }  # Same structure as call
                }
            ],
            'otm_strikes': [  # Strikes at or above spot (Out-of-The-Money for Calls)
                { ... }  # Same structure as itm_strikes
            ],
            'analytics': {
                'atm_strike': float,  # At-The-Money strike (closest to spot)
                'total_call_delta': float,  # Sum of all call deltas
                'total_put_delta': float,  # Sum of all put deltas
                'net_delta': float,  # Net delta exposure (calls + puts)
                'total_strikes': int  # Total number of strikes available
            }
        }
        
        For all expiries (when expiry_date is None):
        {
            'success': True,
            'spot_price': float,
            'expiries': {
                '20251104': {  # Expiry date as key
                    'itm_strikes': [...],
                    'otm_strikes': [...],
                    'analytics': {...}
                },
                '20251202': { ... },
                ...
            }
        }
        
        For errors:
        {
            'success': False,
            'message': str  # Error description
        }
    
    Example Usage:
        # Get latest expiry data with 10 strikes in each direction
        result = process_option_chain_with_analysis('NIFTY', 'NSE', 'latest', 10)
        
        # Get specific expiry
        result = process_option_chain_with_analysis('NIFTY', 'NSE', 20251202, 5)
        
        # Get all expiries
        result = process_option_chain_with_analysis('NIFTY', 'NSE', None, 5)
    """
    try:
        # Convert string to int if necessary for top_n
        try:
            top_n = int(top_n)
        except (ValueError, TypeError):
            return {
                'success': False,
                'message': f"top_n must be a valid integer or string that can be converted to integer. Got: {top_n}"
            }

        # Handle negative top_n
        if top_n < 0:
            return {
                'success': False,
                'message': f"Invalid top_n value: {top_n}. Must be a positive integer."
            }

        # Ensure top_n is at least 1
        if top_n == 0:
            top_n = 1
        
        # Get current spot price
        spot_result = get_current_spot_price(symbol, exchange)
        if not spot_result['success']:
            return {
                'success': False,
                'message': f"Failed to fetch spot price: {spot_result.get('message', 'Unknown error')}"
            }
        
        spot_price = spot_result['spot_price']
        
        # Determine the actual expiry to fetch
        fetch_expiry = None
        is_latest_mode = False
        
        if expiry_date is not None:
            # Check if user wants latest expiry
            if isinstance(expiry_date, str) and expiry_date.lower() == 'latest':
                is_latest_mode = True
                fetch_expiry = None  # Fetch all to find latest
            else:
                # Specific expiry provided
                try:
                    fetch_expiry = int(expiry_date) if isinstance(expiry_date, str) else expiry_date
                except ValueError:
                    return {
                        'success': False,
                        'message': f"Invalid expiry_date format: {expiry_date}. Use integer (YYYYMMDD) or 'latest'"
                    }
        
        # Fetch option chain data
        option_result = fetch_option_chain_data(symbol, exchange, fetch_expiry)
        if not option_result['success']:
            return {
                'success': False,
                'message': f"Failed to fetch option chain: {option_result.get('message', 'Unknown error')}"
            }
        
        raw_data = option_result['data']
        fields = raw_data.get('fields', [])
        symbols_data = raw_data.get('symbols', [])
        
        if not symbols_data:
            return {
                'success': False,
                'message': 'No option data available for the specified parameters'
            }
        
        # Group options by expiry and strike
        expiry_groups = {}
        
        for item in symbols_data:
            symbol_name = item['s']
            values = item['f']
            
            # Map fields to values
            option_data = {}
            for i, field in enumerate(fields):
                option_data[field] = values[i] if i < len(values) else None
            
            strike = option_data.get('strike')
            option_type = option_data.get('option-type')  # 'call' or 'put'
            expiration = option_data.get('expiration')
            
            if strike is None or option_type is None or expiration is None:
                continue
            
            # Initialize expiry group
            if expiration not in expiry_groups:
                expiry_groups[expiration] = {}
            
            # Initialize strike entry
            if strike not in expiry_groups[expiration]:
                expiry_groups[expiration][strike] = {
                    'strike': strike,
                    'call': None,
                    'put': None,
                    'distance_from_spot': abs(strike - spot_price)
                }
            
            # Calculate intrinsic and time value
            if option_type == 'call':
                intrinsic = max(0, spot_price - strike)
            else:  # put
                intrinsic = max(0, strike - spot_price)
            
            theo_price = option_data.get('theoPrice') if option_data.get('theoPrice') else 0
            time_value = theo_price - intrinsic
            
            # Build option info
            option_info = {
                'symbol': symbol_name,
                'ask': option_data.get('ask'),
                'bid': option_data.get('bid'),
                'delta': option_data.get('delta'),
                'gamma': option_data.get('gamma'),
                'theta': option_data.get('theta'),
                'vega': option_data.get('vega'),
                'rho': option_data.get('rho'),
                'iv': option_data.get('iv'),
                'bid_iv': option_data.get('bid_iv'),
                'ask_iv': option_data.get('ask_iv'),
                'theo_price': theo_price,
                'intrinsic_value': round(intrinsic, 2),
                'time_value': round(time_value, 2)
            }
            
            expiry_groups[expiration][strike][option_type] = option_info
        
        # Process each expiry and create flat array
        flat_options = []
        warnings = []

        for expiration, strikes_dict in expiry_groups.items():
            # Sort all strikes
            all_strikes_by_price = sorted(strikes_dict.values(), key=lambda x: x['strike'])

            # Find ATM index
            atm_index = 0
            for i, strike_data in enumerate(all_strikes_by_price):
                if strike_data['strike'] >= spot_price:
                    atm_index = i
                    break

            # Get ITM (below spot) and OTM (above spot) strikes
            available_itm = len(all_strikes_by_price[:atm_index])
            available_otm = len(all_strikes_by_price[atm_index:])

            # Determine actual number to return
            actual_itm = min(top_n, available_itm)
            actual_otm = min(top_n, available_otm)

            itm_strikes = all_strikes_by_price[:atm_index][-actual_itm:] if actual_itm > 0 else []
            otm_strikes = all_strikes_by_price[atm_index:][:actual_otm]

            # Add warnings if insufficient data
            if available_itm < top_n:
                warnings.append(
                    f"Expiry {expiration}: Requested {top_n} ITM strikes but only {available_itm} available"
                )

            if available_otm < top_n:
                warnings.append(
                    f"Expiry {expiration}: Requested {top_n} OTM strikes but only {available_otm} available"
                )

            # Check if top_n is excessive
            total_available = available_itm + available_otm
            if top_n > total_available:
                warnings.append(
                    f"Expiry {expiration}: Cannot return {top_n} strikes in each direction. "
                    f"Total strikes available: {total_available}. Returning all available strikes."
                )

            # Create flat array for this expiry
            for strike_data in itm_strikes + otm_strikes:
                strike = strike_data['strike']
                distance_from_spot = strike_data['distance_from_spot']

                # Add call option if exists
                if strike_data.get('call'):
                    call_option = strike_data['call'].copy()
                    call_option.update({
                        'option': 'call',
                        'strike_price': strike,
                        'distance_from_spot': distance_from_spot
                    })
                    flat_options.append(call_option)

                # Add put option if exists
                if strike_data.get('put'):
                    put_option = strike_data['put'].copy()
                    put_option.update({
                        'option': 'put',
                        'strike_price': strike,
                        'distance_from_spot': distance_from_spot
                    })
                    flat_options.append(put_option)
        
        # Filter options based on expiry_date parameter
        if expiry_date is not None:
            if isinstance(expiry_date, str) and expiry_date.lower() == 'latest':
                # Find latest expiry
                from datetime import datetime
                current_date = int(datetime.now().strftime('%Y%m%d'))
                available_expiries = []
                for opt in flat_options:
                    symbol = opt.get('symbol', '')
                    if 'C' in symbol:
                        expiry_part = symbol.split('C')[0][-8:]
                    elif 'P' in symbol:
                        expiry_part = symbol.split('P')[0][-8:]
                    else:
                        continue
                    try:
                        exp_date = int(expiry_part)
                        if exp_date not in available_expiries:
                            available_expiries.append(exp_date)
                    except ValueError:
                        # Skip invalid expiry dates
                        continue

                available_expiries.sort()
                latest_expiry = None
                for exp in available_expiries:
                    if exp >= current_date:
                        latest_expiry = exp
                        break
                if latest_expiry is None and available_expiries:
                    latest_expiry = available_expiries[-1]

                # Filter for latest expiry
                if latest_expiry is not None:
                    flat_options = [opt for opt in flat_options if str(latest_expiry) in opt.get('symbol', '')]
            else:
                # Specific expiry
                try:
                    target_expiry = str(int(expiry_date)) if isinstance(expiry_date, str) else str(expiry_date)
                    flat_options = [opt for opt in flat_options if target_expiry in opt.get('symbol', '')]
                except ValueError:
                    return [{'success': False, 'message': f'Invalid expiry_date format: {expiry_date}'}]

        # Calculate analytics for the latest expiry (or all data if no specific expiry)
        analytics = {}
        if flat_options:
            # Find the latest expiry from the data
            expiries = set()
            for opt in flat_options:
                symbol = opt.get('symbol', '')
                if 'C' in symbol:
                    expiry_part = symbol.split('C')[0][-8:]
                elif 'P' in symbol:
                    expiry_part = symbol.split('P')[0][-8:]
                else:
                    continue
                try:
                    exp_date = int(expiry_part)
                    expiries.add(exp_date)
                except ValueError:
                    continue

            latest_expiry = max(expiries) if expiries else None

            # Calculate analytics for latest expiry
            latest_expiry_options = [opt for opt in flat_options if str(latest_expiry) in opt.get('symbol', '')]

            total_call_delta = sum(opt.get('delta', 0) for opt in latest_expiry_options if opt.get('option') == 'call')
            total_put_delta = sum(opt.get('delta', 0) for opt in latest_expiry_options if opt.get('option') == 'put')

            # Find ATM strike (closest to spot price)
            if latest_expiry_options:
                atm_strike = min((opt['strike_price'] for opt in latest_expiry_options), key=lambda x: abs(x - spot_price))
            else:
                atm_strike = spot_price

            analytics = {
                'atm_strike': atm_strike,
                'total_call_delta': round(total_call_delta, 4),
                'total_put_delta': round(total_put_delta, 4),
                'net_delta': round(total_call_delta + total_put_delta, 4),
                'total_strikes': len(set(opt['strike_price'] for opt in latest_expiry_options)) if latest_expiry_options else 0
            }

        # Build final result
        result = {
            'success': True,
            'spot_price': spot_price,
            'latest_expiry': latest_expiry if 'latest_expiry' in locals() else None,
            'analytics': analytics,
            'data': flat_options
        }

        # Add warnings if any
        if warnings and 'warnings' not in result:
            result['warnings'] = warnings

        return result
        
    except Exception as e:
        return {'success': False, 'message': f'Failed to process option chain: {str(e)}', 'data': []}
