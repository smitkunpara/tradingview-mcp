"""
Authentication module for TradingView.
Extracts JWT tokens using cookies from environment variables.
"""

import requests
import re
import base64
import json
import os
from typing import Optional, Dict


def extract_jwt_token() -> Optional[str]:
    """
    Extract JWT token from TradingView using cookies from environment variables.
    
    Returns:
        JWT token string if successful, None otherwise
        
    Raises:
        ValueError: If TRADINGVIEW_COOKIE is not set or token extraction fails
    """
    # Check if cookies are set
    cookie = os.getenv("TRADINGVIEW_COOKIE")
    if not cookie:
        raise ValueError(
            "Account is not connected with MCP. Please set TRADINGVIEW_COOKIE "
            "environment variable to connect your account."
        )
    
    # Get URL from environment or use default
    url = os.getenv("TRADINGVIEW_URL", "https://in.tradingview.com/chart/0M7cMdwj/?symbol=NSE%3ANIFTY")
    
    headers = {
        "Host": os.getenv("TRADINGVIEW_HOST", "in.tradingview.com"),
        "Cookie": cookie,
        "User-Agent": os.getenv("TRADINGVIEW_USER_AGENT", 
                                "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Priority": "u=0, i",
        "Te": "trailers"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html_content = response.text

        jwt_pattern = r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'
        potential_tokens = re.findall(jwt_pattern, html_content)

        def verify_jwt(token: str) -> bool:
            """Verify if a token is a valid JWT structure."""
            try:
                parts = token.split('.')
                if len(parts) != 3:
                    return False
                header_b64, payload_b64, _ = parts
                # Add padding if needed
                header_b64 += '=' * (4 - len(header_b64) % 4)
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                header_json = base64.urlsafe_b64decode(header_b64)
                payload_json = base64.urlsafe_b64decode(payload_b64)
                header = json.loads(header_json)
                payload = json.loads(payload_json)
                # Check if header has 'alg' and 'typ'
                if 'alg' not in header or 'typ' not in header:
                    return False
                return True
            except Exception:
                return False

        for token in potential_tokens:
            if verify_jwt(token):
                return token
        
        raise ValueError(
            "Token is not generated with cookies. Please verify your cookies "
            "and ensure they are valid and not expired."
        )
        
    except requests.RequestException as e:
        raise ValueError(
            f"Failed to extract JWT token from TradingView: {str(e)}. "
            "Please verify your cookies and network connection."
        )


def get_token_info(token: str) -> Dict:
    """
    Decode JWT token and extract expiry information.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with token info including expiry timestamp
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {'valid': False, 'error': 'Invalid token format'}
        
        payload_b64 = parts[1]
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        
        return {
            'valid': True,
            'exp': payload.get('exp'),
            'iat': payload.get('iat'),
            'user_id': payload.get('user_id')
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}