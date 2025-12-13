"""
Tests for /news-headlines endpoint.
Mirrors tests/stdio/test_fetch_news_headlines.py
"""

import pytest
from toon import decode as toon_decode

class TestNewsHeadlinesEndpoint:
    """Test /news-headlines endpoint with real data"""
    
    def test_basic_news_fetch(self, client, auth_headers):
        """Test fetching news headlines"""
        payload = {
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "provider": "all",
            "area": "americas"
        }
        
        response = client.post("/news-headlines", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        headlines = data.get("headlines", [])
        
        assert isinstance(headlines, list)
        if len(headlines) > 0:
            headline = headlines[0]
            assert 'title' in headline
            assert 'storyPath' in headline or 'url' in headline

    def test_news_different_providers(self, client, auth_headers):
        """Test with different news providers"""
        providers = ['all', 'dow-jones', 'tradingview']
        
        for provider in providers:
            payload = {
                "symbol": "BTCUSD",
                "exchange": "BITSTAMP",
                "provider": provider,
                "area": "world"
            }
            
            response = client.post("/news-headlines", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert isinstance(data.get("headlines"), list)

    def test_news_different_areas(self, client, auth_headers):
        """Test with different geographical areas"""
        areas = ['world', 'americas', 'europe', 'asia']
        
        for area in areas:
            payload = {
                "symbol": "NIFTY",
                "exchange": "NSE",
                "provider": "all",
                "area": area
            }
            
            response = client.post("/news-headlines", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert isinstance(data.get("headlines"), list)

    def test_invalid_area(self, client, auth_headers):
        """Test with invalid area"""
        payload = {
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "provider": "all",
            "area": "invalid_area"
        }
        
        response = client.post("/news-headlines", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        detail = str(response.json()["detail"])
        assert "Area" in detail or "area" in detail

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "AAPL",
            "exchange": "INVALID_EXCHANGE",
            "provider": "all",
            "area": "americas"
        }
        
        response = client.post("/news-headlines", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]
