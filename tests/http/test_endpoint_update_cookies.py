"""
Tests for /update-cookies endpoint.
"""

import pytest
from unittest.mock import patch, MagicMock

class TestUpdateCookiesEndpoint:
    """Test /update-cookies endpoint"""
    
    def test_update_cookies_success(self, client, admin_headers):
        """Test successful cookie update with valid admin key"""
        payload = {
            "cookies": [{"name": "test_cookie", "value": "test_value"}],
            "source": "test_runner"
        }
        
        # Mock fetch_ideas to return success so validation passes
        # Mock settings.update_cookie to avoid writing to .env
        with patch("vercel.index.fetch_ideas", return_value={"success": True}) as mock_fetch, \
             patch("vercel.index.settings.update_cookie") as mock_update:
            
            response = client.post("/update-cookies", json=payload, headers=admin_headers)
            
            assert response.status_code == 200
            assert response.json()["success"] == True
            assert "verified and updated" in response.json()["message"]
            
            # Verify mock calls
            mock_fetch.assert_called()
            mock_update.assert_called_with("test_cookie=test_value")

    def test_update_cookies_unauthorized(self, client):
        """Test update without admin key"""
        payload = {
            "cookies": [{"name": "test_cookie", "value": "test_value"}]
        }
        
        response = client.post("/update-cookies", json=payload)
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"]

    def test_update_cookies_invalid_key(self, client):
        """Test update with invalid admin key"""
        payload = {
            "cookies": [{"name": "test_cookie", "value": "test_value"}]
        }
        
        response = client.post("/update-cookies", json=payload, headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"]

    def test_update_cookies_validation_failure(self, client, admin_headers):
        """Test update when cookie validation fails"""
        payload = {
            "cookies": [{"name": "bad_cookie", "value": "bad_value"}]
        }
        
        # Mock fetch_ideas to return failure
        with patch("vercel.index.fetch_ideas", return_value={"success": False}) as mock_fetch, \
             patch("vercel.index.settings.update_cookie") as mock_update:
            
            response = client.post("/update-cookies", json=payload, headers=admin_headers)
            
            assert response.status_code == 200  # Endpoint returns 200 even on failure logic
            assert response.json()["success"] == False
            assert "validation failed" in response.json()["message"]
            
            mock_update.assert_not_called()

    def test_update_cookies_no_cookies(self, client, admin_headers):
        """Test update with empty cookies"""
        payload = {
            "cookies": [],
            "source": "test"
        }
        
        response = client.post("/update-cookies", json=payload, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["success"] == False
        assert "No cookies provided" in response.json()["message"]
