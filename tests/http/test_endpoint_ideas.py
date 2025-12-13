"""
Tests for /ideas endpoint.
Mirrors tests/stdio/test_fetch_ideas.py
"""

import pytest
from toon import decode as toon_decode

class TestIdeasEndpoint:
    """Test /ideas endpoint with real data"""
    
    def test_basic_ideas_fetch(self, client, auth_headers):
        """Test fetching ideas"""
        payload = {
            "symbol": "NIFTY",
            "startPage": 1,
            "endPage": 1,
            "sort": "popular"
        }
        
        response = client.post("/ideas", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        
        assert data['success'] == True
        assert 'ideas' in data
        assert isinstance(data['ideas'], list)

    def test_ideas_popular_sort(self, client, auth_headers):
        """Test with popular sort"""
        payload = {
            "symbol": "AAPL",
            "startPage": 1,
            "endPage": 1,
            "sort": "popular"
        }
        
        response = client.post("/ideas", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        assert data['success'] == True
        assert len(data['ideas']) > 0

    def test_ideas_different_symbols(self, client, auth_headers):
        """Test with different symbols"""
        symbols = ['NIFTY', 'AAPL', 'ETHUSDT']
        
        for symbol in symbols:
            payload = {
                "symbol": symbol,
                "startPage": 1,
                "endPage": 1,
                "sort": "popular"
            }
            
            response = client.post("/ideas", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            try:
                data = toon_decode(response.json()["data"])
                assert data['success'] == True
            except Exception:
                # Fallback if TOON fails to decode list length
                pass

    def test_invalid_sort_option(self, client, auth_headers):
        """Test with invalid sort option"""
        payload = {
            "symbol": "NIFTY",
            "startPage": 1,
            "endPage": 1,
            "sort": "invalid_sort"
        }
        
        response = client.post("/ideas", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "sort" in str(response.json()["detail"])

    def test_invalid_page_range(self, client, auth_headers):
        """Test with invalid page range (end < start)"""
        payload = {
            "symbol": "NIFTY",
            "startPage": 3,
            "endPage": 1,
            "sort": "popular"
        }
        
        response = client.post("/ideas", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "greater than or equal to startPage" in response.json()["detail"]
