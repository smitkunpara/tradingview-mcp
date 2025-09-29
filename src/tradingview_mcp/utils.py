"""
Utility functions for TradingView MCP server.
"""

from datetime import datetime
import pytz
from typing import Any, Dict, List
from bs4 import Tag, NavigableString
from .validators import INDICATOR_MAPPING, INDICATOR_FIELD_MAPPING


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
    
    # Extract all available indicators (limited to max 2 for free accounts)
    available_indicators = {}
    indicator_count = 0
    max_indicators = 2  # Free account limitation
    
    for indicator_short, (indicator_key, _) in INDICATOR_MAPPING.items():
        if indicator_count >= max_indicators:
            break  # Respect free account limits
            
        for indicator_name, indicator_values in indicator_data.items():
            if indicator_key == indicator_name:
                available_indicators[indicator_short] = indicator_values
                indicator_count += 1
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
    
    # Prepare indicator data matched to OHLC length
    matched_indicators = {}
    for indicator_short, indicator_values in available_indicators.items():
        matched_indicators[indicator_short] = indicator_values[:len(ohlc_data)]
    
    # Create merged data structure
    merged_data = []
    
    for i, ohlc_entry in enumerate(ohlc_data):
        ohlc_timestamp = ohlc_entry.get('timestamp')
        
        # Validate timestamps match for all indicators
        for indicator_short, indicator_values in matched_indicators.items():
            if i < len(indicator_values):
                indicator_entry = indicator_values[i]
                indicator_timestamp = indicator_entry.get('timestamp')
                
                if ohlc_timestamp != indicator_timestamp:
                    raise ValueError(
                        f"Timestamp mismatch from TradingView at index {i}. "
                        f"OHLC timestamp: {ohlc_timestamp}, {indicator_short} timestamp: {indicator_timestamp}. "
                        f"Data synchronization error."
                    )
        
        # Convert timestamp to Indian time
        datetime_ist = convert_timestamp_to_indian_time(ohlc_timestamp)
        
        # Create base merged entry
        merged_entry = {
            "open": ohlc_entry.get('open'),
            "high": ohlc_entry.get('high'),
            "low": ohlc_entry.get('low'),
            "close": ohlc_entry.get('close'),
            "volume": ohlc_entry.get('volume'),
            "index": ohlc_entry.get('index'),
            "datetime_ist": datetime_ist
        }
        
        # Add all available indicator values
        for indicator_short, indicator_values in matched_indicators.items():
            if i < len(indicator_values):
                indicator_entry = indicator_values[i]
                field_mapping = INDICATOR_FIELD_MAPPING[indicator_short]
                
                # Add each field for this indicator
                for index_key, field_name in field_mapping.items():
                    value = indicator_entry.get(index_key, 0)
                    merged_entry[field_name] = value
        
        merged_data.append(merged_entry)
    
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