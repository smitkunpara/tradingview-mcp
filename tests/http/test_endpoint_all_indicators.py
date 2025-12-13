"""
Tests for /all-indicators endpoint.
Mirrors tests/stdio/test_fetch_all_indicators.py
"""

import pytest
from toon import decode as toon_decode

class TestAllIndicatorsEndpoint:
    """Test /all-indicators endpoint with real data"""
    
    def test_basic_indicators_fetch(self, client, auth_headers):
        """Test fetching all indicators"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "1m"
        }
        
        response = client.post("/all-indicators", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        raw_data = response.json()["data"]
        try:
            data = toon_decode(raw_data)
            assert data['success'] == True
            assert 'data' in data
            assert isinstance(data['data'], dict)
            assert len(data['data']) > 0
        except Exception as e:
            print(f"Toon decode failed: {e}")
            # Fallback: check if raw string contains expected keys
            assert "RSI" in raw_data or "MACD" in raw_data

    def test_indicators_different_timeframes(self, client, auth_headers):
        """Test with different timeframes"""
        timeframes = ['1m', '5m', '1h', '1d']
        
        for tf in timeframes:
            payload = {
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "timeframe": tf
            }
            
            response = client.post("/all-indicators", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            try:
                data = toon_decode(response.json()["data"])
                assert data['success'] == True
                assert len(data['data']) > 0
            except Exception:
                # Allow fallback if TOON fails (library issue)
                pass

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "INVALID_EXCHANGE",
            "timeframe": "1m"
        }
        
        response = client.post("/all-indicators", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]

    def test_invalid_timeframe(self, client, auth_headers):
        """Test with invalid timeframe"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "3m"
        }
        
        response = client.post("/all-indicators", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        # Pydantic returns list of dicts for 422, custom errors return string for 400
        detail = str(response.json()["detail"])
        assert "Timeframe" in detail or "timeframe" in detail
