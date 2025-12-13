"""
Tests for /option-chain-greeks endpoint.
Mirrors tests/stdio/test_fetch_option_chain.py
"""

import pytest
from toon import decode as toon_decode

class TestOptionChainEndpoint:
    """Test /option-chain-greeks endpoint with real data"""
    
    def test_basic_option_chain_nearest(self, client, auth_headers):
        """Test basic option chain data fetch with nearest expiry"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": "nearest",
            "no_of_ITM": 5,
            "no_of_OTM": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        
        assert data['success'] == True
        assert 'data' in data
        assert 'available_expiries' in data
        assert data['requested_ITM'] == 5
        assert data['requested_OTM'] == 5
        
        # Verify only one expiry in returned data using 'expiration' field
        expiries_in_data = set(opt.get('expiration') for opt in data['data'] if opt.get('expiration'))
        
        assert len(expiries_in_data) == 1, "Should only have one expiry for 'nearest' mode"

    def test_option_chain_all_expiries(self, client, auth_headers):
        """Test with all expiries"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": "all",
            "no_of_ITM": 3,
            "no_of_OTM": 3
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        assert data['success'] == True
        assert len(data['available_expiries']) > 1, "Should have multiple expiries"

    def test_option_chain_specific_expiry(self, client, auth_headers):
        """Test with specific expiry date"""
        # First get available expiries
        payload_all = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": "all",
            "no_of_ITM": 1,
            "no_of_OTM": 1
        }
        
        response_all = client.post("/option-chain-greeks", json=payload_all, headers=auth_headers)
        assert response_all.status_code == 200
        data_all = toon_decode(response_all.json()["data"])
        assert len(data_all['available_expiries']) > 0
        
        # Test with specific expiry
        specific_expiry = data_all['available_expiries'][0]
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": specific_expiry,
            "no_of_ITM": 5,
            "no_of_OTM": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        assert data['success'] == True
        assert specific_expiry in data['available_expiries']

    def test_option_chain_invalid_expiry(self, client, auth_headers):
        """Test with invalid expiry - should return available expiries"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "expiry_date": 20991231,  # Far future date
            "no_of_ITM": 5,
            "no_of_OTM": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = toon_decode(response.json()["data"])
        assert data['success'] == False
        assert 'available_expiries' in data
        assert 'not found' in data['message'].lower()

    def test_option_chain_different_itm_otm(self, client, auth_headers):
        """Test with different ITM/OTM values"""
        test_cases = [
            (3, 3),
            (5, 5),
            (10, 5),
            (2, 8)
        ]
        
        for itm, otm in test_cases:
            payload = {
                "symbol": "NIFTY",
                "exchange": "NSE",
                "expiry_date": "nearest",
                "no_of_ITM": itm,
                "no_of_OTM": otm
            }
            
            response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
            assert response.status_code == 200
            
            data = toon_decode(response.json()["data"])
            assert data['success'] == True
            assert data['requested_ITM'] == itm
            assert data['requested_OTM'] == otm

    def test_invalid_exchange(self, client, auth_headers):
        """Test with invalid exchange"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "INVALID_EXCHANGE",
            "no_of_ITM": 5,
            "no_of_OTM": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "Exchange" in response.json()["detail"] or "exchange" in response.json()["detail"]

    def test_invalid_itm_too_high(self, client, auth_headers):
        """Test with no_of_ITM exceeding limit"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "no_of_ITM": 25,
            "no_of_OTM": 5
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "between 1 and 20" in response.json()["detail"]
    
    def test_invalid_otm_zero(self, client, auth_headers):
        """Test with zero no_of_OTM"""
        payload = {
            "symbol": "NIFTY",
            "exchange": "NSE",
            "no_of_ITM": 5,
            "no_of_OTM": 0
        }
        
        response = client.post("/option-chain-greeks", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]
        assert "between 1 and 20" in response.json()["detail"]
