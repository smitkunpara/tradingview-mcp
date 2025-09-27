"""
Utility functions for TradingView MCP server.
"""

from datetime import datetime
import pytz
from typing import Any, Dict, List
from bs4 import Tag, NavigableString


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
    Merge OHLC data with RSI indicator data by matching timestamps.
    Creates a unified structure with RSI values embedded in OHLC records.
    
    Args:
        data: Data structure with OHLC and indicator data
        
    Returns:
        Merged OHLC data with RSI values embedded
        
    Raises:
        ValueError: If timestamps don't match or data is invalid
    """
    ohlc_data = data.get('ohlc', [])
    indicator_data = data.get('indicator', {})
    
    if not ohlc_data:
        raise ValueError("No OHLC data found in response from TradingView")
    
    # Get RSI data (assuming only RSI indicator for now)
    rsi_data = None
    for indicator_name, indicator_values in indicator_data.items():
        if 'RSI' in indicator_name:
            rsi_data = indicator_values
            break
    
    if not rsi_data:
        # Return OHLC data without indicators if no RSI found
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
    
    # Take only the first N RSI entries to match OHLC length
    rsi_data_matched = rsi_data[:len(ohlc_data)]
    
    if len(ohlc_data) != len(rsi_data_matched):
        raise ValueError(
            f"Data length mismatch from TradingView: OHLC has {len(ohlc_data)} records, "
            f"RSI has {len(rsi_data_matched)} records. Unable to merge indicators."
        )
    
    # Create merged data structure
    merged_data = []
    
    for i, ohlc_entry in enumerate(ohlc_data):
        rsi_entry = rsi_data_matched[i]
        
        # Validate timestamps match
        ohlc_timestamp = ohlc_entry.get('timestamp')
        rsi_timestamp = rsi_entry.get('timestamp')
        
        if ohlc_timestamp != rsi_timestamp:
            raise ValueError(
                f"Timestamp mismatch from TradingView at index {i}. "
                f"OHLC timestamp: {ohlc_timestamp}, RSI timestamp: {rsi_timestamp}. "
                f"Data synchronization error."
            )
        
        # Convert timestamp to Indian time
        datetime_ist = convert_timestamp_to_indian_time(ohlc_timestamp)
        
        # Create merged entry
        merged_entry = {
            "open": ohlc_entry.get('open'),
            "high": ohlc_entry.get('high'),
            "low": ohlc_entry.get('low'),
            "close": ohlc_entry.get('close'),
            "volume": ohlc_entry.get('volume'),
            "index": ohlc_entry.get('index'),
            "datetime_ist": datetime_ist,
            "RSI": rsi_entry.get('2', 0),  # RSI value is typically at key '2'
            "moving_average_RSI": rsi_entry.get('0', 0)  # Moving average RSI at key '0'
        }
        
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