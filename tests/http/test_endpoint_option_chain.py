"""
Tests for /option-chain-greeks endpoint.
Mirrors tests/stdio/test_fetch_option_chain.py
"""

import pytest
from toon import decode as toon_decode

class TestOptionChainEndpoint:
    """Test /option-chain-greeks endpoint with real data"""
    
    def test_basic_option_chain_fetch(self, client, auth_headers):
        """Test basic option chain data fetch"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": None,
            "top_n": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        
        assert data['success'] == True
        assert 'data' in data

    def test_option_chain_specific_expiry(self, client, auth_headers):
        """Test with specific expiry date"""
        # Using a dummy expiry, the backend might return empty data (success=False) but should respond
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": 20251202,
            "top_n": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        # API returns success=False if no data found for expiry, which is expected behavior
        assert isinstance(data.get('success'), bool)

    def test_option_chain_different_top_n(self, client, auth_headers):
        """Test with different top_n values"""
        top_n_values = [3, 5, 10]
        
        for top_n in top_n_values:
            payload = {
                "symbol": "NIFTY",
                "exchange": "NSE",
                "expiry_date": None,
                "top_n": top_n
            }
            
            response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert data['success'] == True

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "INVALID_EXCHANGE",
            "top_n": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]

    def test_invalid_top_n_too_high(self, client, auth_headers):
        """Test with top_n exceeding limit"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "top_n": 25
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "between 1 and 20" in response.json()["detail"]
