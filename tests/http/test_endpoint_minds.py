"""
Tests for /minds endpoint.
Mirrors tests/stdio/test_fetch_minds.py
"""

import pytest
from toon import decode as toon_decode

class TestMindsEndpoint:
    """Test /minds endpoint with real data"""
    
    def test_basic_minds_fetch(self, client, auth_headers):
        """Test fetching minds discussions"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "limit": 10
        }
        
        response = client.post("/minds", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        
        assert data['success'] == True
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_minds_with_no_limit(self, client, auth_headers):
        """Test with default limit (None)"""
        payload = {
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "limit": None
        }
        
        response = client.post("/minds", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        assert data['success'] == True
        assert isinstance(data['data'], list)

    def test_minds_different_symbols(self, client, auth_headers):
        """Test with different symbols"""
        symbols = [
            ('NIFTY', 'NSE'),
            ('BTCUSD', 'BINANCE'),
            ('AAPL', 'NASDAQ')
        ]
        
        for symbol, exchange in symbols:
            payload = {
                "symbol": symbol,
                "exchange": exchange,
                "limit": 5
            }
            
            response = client.post("/minds", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert data['success'] == True

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "INVALID_EXCHANGE",
            "limit": 10
        }
        
        response = client.post("/minds", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]

    def test_invalid_limit_negative(self, client, auth_headers):
        """Test with negative limit"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "limit": -5
        }
        
        response = client.post("/minds", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "positive integer" in response.json()["detail"]

    def test_invalid_limit_zero(self, client, auth_headers):
        """Test with zero limit"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "limit": 0
        }
        
        response = client.post("/minds", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "positive integer" in response.json()["detail"]
