"""
Utility functions for TradingView MCP server.
"""

from datetime import datetime
import pytz
from typing import Any, Dict, List
from bs4 import Tag, NavigableString
from tradingview_mcp.validators import INDICATOR_MAPPING, INDICATOR_FIELD_MAPPING


def convert_timestamp_to_indian_time(timestamp: float) -> str:
    """
    Convert Unix timestamp to Indian date/time in 12-hour format.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted Indian date/time string (DD-MM-YYYY HH:MM:SS AM/PM IST)
    """
    # Convert timestamp to datetime object in UTC
    utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    
    # Convert to Indian Standard Time (IST)
    ist = pytz.timezone('Asia/Kolkata')
    indian_dt = utc_dt.astimezone(ist)
    
    # Format in 12-hour format with AM/PM
    formatted_time = indian_dt.strftime("%d-%m-%Y %I:%M:%S %p IST")
    return formatted_time


def clean_for_json(obj: Any) -> Any:
    """
    Convert BeautifulSoup objects to JSON-serializable format.
    
    Args:
        obj: Object to clean (can be dict, list, or BeautifulSoup objects)
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (Tag, NavigableString)):
        return str(obj)  # Convert any BeautifulSoup object to string
    else:
        return obj


def merge_ohlc_with_indicators(data: Dict) -> List[Dict]:
    """
    Merge OHLC data with multiple technical indicators by matching timestamps.
    Creates a unified structure with indicator values embedded in OHLC records.
    
    Supports indicators: RSI, MACD, CCI, and Bollinger Bands
    Note: Free TradingView accounts are limited to maximum 2 indicators per request
    
    Args:
        data: Data structure with OHLC and indicator data
        
    Returns:
        Merged OHLC data with indicator values embedded
        
    Raises:
        ValueError: If timestamps don't match or data is invalid
    """
    ohlc_data = data.get('ohlc', [])
    indicator_data = data.get('indicator', {})
    
    if not ohlc_data:
        raise ValueError("No OHLC data found in response from TradingView. Please verify the JWT token and parameters.")
    
    # Combine all indicator arrays provided. The caller may supply indicator
    # data collected across multiple batched requests; these will all appear
    # under the "indicator" dict keyed by TradingView indicator keys.
    available_indicators = {}
    for indicator_short, (indicator_key, _) in INDICATOR_MAPPING.items():
        # If indicator present under the tradingview key, take its array
        for indicator_name, indicator_values in indicator_data.items():
            if indicator_key == indicator_name:
                # Ensure we copy the list to avoid mutating caller data
                available_indicators[indicator_short] = list(indicator_values)
                break
    
    if not available_indicators:
        # Return OHLC data without indicators if none found
        merged_data = []
        for ohlc_entry in ohlc_data:
            datetime_ist = convert_timestamp_to_indian_time(ohlc_entry.get('timestamp'))
            merged_entry = {
                "open": ohlc_entry.get('open'),
                "high": ohlc_entry.get('high'),
                "low": ohlc_entry.get('low'),
                "close": ohlc_entry.get('close'),
                "volume": ohlc_entry.get('volume'),
                "index": ohlc_entry.get('index'),
                "datetime_ist": datetime_ist
            }
            merged_data.append(merged_entry)
        return merged_data
    
    # We'll match indicator entries to OHLC candles by timestamp. Since
    # indicators may come from multiple requests and may include one extra
    # candle to avoid conflicts, do a timestamp-based lookup instead of
    # position-based strict equality. Collect any mismatches as warnings
    # (returned via a special _errors key inside merged entries list metadata
    # if needed by callers).

    # Build a mapping from ohlc timestamp -> index in ohlc_data
    ohlc_index_by_ts = {entry.get('timestamp'): idx for idx, entry in enumerate(ohlc_data)}

    # Prepare per-indicator maps: indicator_short -> {timestamp: entry}
    indicator_maps = {}
    for indicator_short, indicator_values in available_indicators.items():
        ts_map = {}
        for item in indicator_values:
            ts = item.get('timestamp')
            if ts is not None:
                # If duplicate timestamps exist, prefer the earliest occurrence
                if ts not in ts_map:
                    ts_map[ts] = item
        indicator_maps[indicator_short] = ts_map

    merged_data = []
    errors = []

    for i, ohlc_entry in enumerate(ohlc_data):
        ohlc_timestamp = ohlc_entry.get('timestamp')
        datetime_ist = convert_timestamp_to_indian_time(ohlc_timestamp)

        merged_entry = {
            "open": ohlc_entry.get('open'),
            "high": ohlc_entry.get('high'),
            "low": ohlc_entry.get('low'),
            "close": ohlc_entry.get('close'),
            "volume": ohlc_entry.get('volume'),
            "index": ohlc_entry.get('index'),
            "datetime_ist": datetime_ist
        }

        # For each indicator, look up by timestamp; if not present, try to
        # find by close nearby offsets (1 or 2 positions) — BUT do not raise
        # errors. Instead record a warning and continue.
        for indicator_short, ts_map in indicator_maps.items():
            indicator_entry = ts_map.get(ohlc_timestamp)

            if indicator_entry is None:
                # not found at exact timestamp; we won't attempt complex
                # scanning here. Caller fetch logic ensures extra candles are
                # included; if missing, just log and continue.
                errors.append(
                    f"Indicator '{indicator_short}' missing for OHLC timestamp {ohlc_timestamp} (index {i})"
                )
                continue

            field_mapping = INDICATOR_FIELD_MAPPING.get(indicator_short, {})
            for index_key, field_name in field_mapping.items():
                value = indicator_entry.get(index_key, 0)
                merged_entry[field_name] = value

        merged_data.append(merged_entry)

    # Optionally attach errors in a way the caller can pick up. We won't
    # change the return type, but callers that need error details may look
    # for a top-level '_merge_errors' key on the returned list object via
    # an attribute. Python lists can't have attributes, so instead we will
    # append a final dict with a reserved key when there are errors.
    if errors:
        merged_data.append({"_merge_errors": errors})

    return merged_data


def extract_news_body(content: Dict) -> str:
    """
    Extract text body from news content.
    
    Args:
        content: News content dictionary
        
    Returns:
        Extracted text body as string
    """
    body = ""
    for data in content.get("body", []):
        if data.get("type") == "text":
            body += data.get("content", "") + "\n"
    return body.strip()