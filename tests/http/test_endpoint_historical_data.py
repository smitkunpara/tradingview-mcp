"""
Tests for /historical-data endpoint.
Mirrors tests/stdio/test_fetch_historical_data.py
"""

import pytest
from toon import decode as toon_decode

class TestHistoricalDataEndpoint:
    """Test /historical-data endpoint with real data"""
    
    def test_basic_ohlc_without_indicators(self, client, auth_headers):
        """Test fetching basic OHLC data without indicators"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "1m",
            "numb_price_candles": 10,
            "indicators": []
        }
        
        response = client.post("/historical-data", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        # Decode TOON response
        json_resp = response.json()
        assert "data" in json_resp
        data = toon_decode(json_resp["data"])
        
        assert data['success'] == True
        assert 'data' in data
        assert len(data['data']) > 0
        
        # Check OHLC structure
        first_candle = data['data'][0]
        assert 'open' in first_candle
        assert 'high' in first_candle
        assert 'low' in first_candle
        assert 'close' in first_candle
        assert 'volume' in first_candle
        assert 'datetime_ist' in first_candle or 'timestamp' in first_candle

    def test_ohlc_with_single_indicator(self, client, auth_headers):
        """Test with single indicator (RSI)"""
        payload = {
            "symbol": "BTCUSD",
            "exchange": "BINANCE",
            "timeframe": "5m",
            "numb_price_candles": 20,
            "indicators": ["RSI"]
        }
        
        response = client.post("/historical-data", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        
        assert data['success'] == True
        assert len(data['data']) > 0
        
        first_candle = data['data'][0]
        has_rsi = any('RSI' in key or 'Relative_Strength_Index' in key for key in first_candle.keys())
        assert has_rsi, "RSI indicator not found in data"

    def test_ohlc_different_timeframes(self, client, auth_headers):
        """Test with different timeframes"""
        timeframes = ['1m', '5m', '15m', '1h', '1d']
        
        for tf in timeframes:
            payload = {
                "symbol": "AAPL",
                "exchange": "NASDAQ",
                "timeframe": tf,
                "numb_price_candles": 5,
                "indicators": []
            }
            
            response = client.post("/historical-data", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert data['success'] == True
            assert len(data['data']) > 0

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "INVALID_EXCHANGE",
            "timeframe": "1m",
            "numb_price_candles": 10,
            "indicators": []
        }
        
        response = client.post("/historical-data", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]

    def test_invalid_timeframe(self, client, auth_headers):
        """Test with invalid timeframe"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "3m",
            "numb_price_candles": 10,
            "indicators": []
        }
        
        response = client.post("/historical-data", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        detail = str(response.json()["detail"])
        assert "Timeframe" in detail or "timeframe" in detail

    def test_invalid_candle_count(self, client, auth_headers):
        """Test with invalid number of candles"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "1m",
            "numb_price_candles": 6000,
            "indicators": []
        }
        
        response = client.post("/historical-data", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "between 1 and 5000" in response.json()["detail"]

    def test_unauthorized(self, client):
        """Test without auth headers"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "timeframe": "1m",
            "numb_price_candles": 10,
            "indicators": []
        }
        
        response = client.post("/historical-data", json=payload)
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"]
