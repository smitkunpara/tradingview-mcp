"""
Tests for /news-content endpoint.
Mirrors tests/stdio/test_fetch_news_content.py
"""

import pytest
from toon import decode as toon_decode

class TestNewsContentEndpoint:
    """Test /news-content endpoint with real data"""
    
    def test_basic_news_content_fetch(self, client, auth_headers):
        """Test fetching news content from headlines"""
        # First get headlines
        hl_payload = {
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "provider": "all",
            "area": "americas"
        }
        hl_response = client.post("/news-headlines", json=hl_payload, headers=auth_headers)
        hl_data = toon_decode(hl_response.json()["data"])
        headlines = hl_data.get("headlines", [])
        
        if len(headlines) > 0 and 'storyPath' in headlines[0]:
            story_path = headlines[0]['storyPath']
            
            # Fetch content
            payload = {"story_paths": [story_path]}
            response = client.post("/news-content", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            articles = data.get("articles", [])
            
            assert isinstance(articles, list)
            assert len(articles) > 0
            
            content = articles[0]
            assert 'success' in content

    def test_news_content_multiple_stories(self, client, auth_headers):
        """Test with multiple story paths"""
        # Get multiple story paths
        hl_payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "provider": "all",
            "area": "asia"
        }
        hl_response = client.post("/news-headlines", json=hl_payload, headers=auth_headers)
        hl_data = toon_decode(hl_response.json()["data"])
        headlines = hl_data.get("headlines", [])
        
        story_paths = [h['storyPath'] for h in headlines[:3] if 'storyPath' in h]
        
        if len(story_paths) > 0:
            payload = {"story_paths": story_paths}
            response = client.post("/news-content", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            articles = data.get("articles", [])
            
            assert isinstance(articles, list)
            assert len(articles) <= len(story_paths)

    def test_empty_story_paths(self, client, auth_headers):
        """Test with empty story paths list"""
        payload = {"story_paths": []}
        response = client.post("/news-content", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "story_paths" in str(response.json()["detail"])
