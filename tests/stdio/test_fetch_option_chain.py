"""
Real tests for fetch_option_chain functions.
Tests with actual TradingView data - no mocks.
"""

import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tradingview_mcp.tradingview_tools import fetch_option_chain_data, process_option_chain_with_analysis
from tradingview_mcp.validators import ValidationError


class TestFetchOptionChain:
    """Test option chain functions with real data"""
    
    def test_basic_option_chain_fetch(self):
        """Test basic option chain data fetch"""
        result = fetch_option_chain_data(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date=None
        )
        
        assert result['success'] == True
        assert 'data' in result
    
    def test_option_chain_with_nearest_expiry(self):
        """Test option chain with nearest expiry"""
        result = process_option_chain_with_analysis(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date='nearest',
            no_of_ITM=5,
            no_of_OTM=5
        )
        
        assert result['success'] == True
        assert 'spot_price' in result
        assert 'available_expiries' in result
        assert 'data' in result
        assert result['requested_ITM'] == 5
        assert result['requested_OTM'] == 5
        assert len(result['data']) > 0
        
        # Verify we only have one expiry in the data using 'expiration' field
        expiries_in_data = set(opt.get('expiration') for opt in result['data'] if opt.get('expiration'))
        
        assert len(expiries_in_data) == 1, "Should only have one expiry for 'nearest' mode"
    
    def test_option_chain_with_all_expiries(self):
        """Test option chain with all expiries"""
        result = process_option_chain_with_analysis(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date='all',
            no_of_ITM=3,
            no_of_OTM=3
        )
        
        assert result['success'] == True
        assert 'available_expiries' in result
        assert len(result['available_expiries']) > 1, "Should have multiple expiries"
        
        # Verify we have multiple expiries in the data using 'expiration' field
        expiries_in_data = set(opt.get('expiration') for opt in result['data'] if opt.get('expiration'))
        
        assert len(expiries_in_data) > 1, "Should have multiple expiries for 'all' mode"
    
    def test_option_chain_specific_expiry(self):
        """Test with specific expiry date"""
        # First get available expiries
        result_all = process_option_chain_with_analysis(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date='all',
            no_of_ITM=1,
            no_of_OTM=1
        )
        
        assert result_all['success'] == True
        assert len(result_all['available_expiries']) > 0
        
        # Now test with a specific expiry
        specific_expiry = result_all['available_expiries'][0]
        result = process_option_chain_with_analysis(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date=specific_expiry,
            no_of_ITM=5,
            no_of_OTM=5
        )
        
        assert result['success'] == True
        assert specific_expiry in result['available_expiries']
    
    def test_option_chain_invalid_expiry(self):
        """Test with invalid expiry - should return available expiries"""
        result = process_option_chain_with_analysis(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date=20991231,  # Far future date that doesn't exist
            no_of_ITM=5,
            no_of_OTM=5
        )
        
        assert result['success'] == False
        assert 'available_expiries' in result
        assert 'not found' in result['message'].lower()
    
    def test_option_chain_different_itm_otm(self):
        """Test with different ITM/OTM values"""
        test_cases = [
            (3, 3),
            (5, 5),
            (10, 5),
            (2, 8)
        ]
        
        for itm, otm in test_cases:
            result = process_option_chain_with_analysis(
                symbol='NIFTY',
                exchange='NSE',
                expiry_date='nearest',
                no_of_ITM=itm,
                no_of_OTM=otm
            )
            
            assert result['success'] == True
            assert result['requested_ITM'] == itm
            assert result['requested_OTM'] == otm
            print(f"✓ ITM={itm}, OTM={otm} works - returned {len(result['data'])} options")
    
    def test_option_chain_banknifty(self):
        """Test with BANKNIFTY symbol"""
        result = process_option_chain_with_analysis(
            symbol='BANKNIFTY',
            exchange='NSE',
            expiry_date='nearest',
            no_of_ITM=5,
            no_of_OTM=5
        )
        
        assert result['success'] == True
        assert 'spot_price' in result
    
    def test_invalid_exchange(self):
        """Test with invalid exchange"""
        with pytest.raises(ValidationError):
            process_option_chain_with_analysis(
                symbol='NIFTY',
                exchange='INVALID_EXCHANGE',
                expiry_date='nearest',
                no_of_ITM=5,
                no_of_OTM=5
            )
    
    def test_invalid_itm_zero(self):
        """Test with zero no_of_ITM"""
        with pytest.raises(ValidationError):
            process_option_chain_with_analysis(
                symbol='NIFTY',
                exchange='NSE',
                expiry_date='nearest',
                no_of_ITM=0,
                no_of_OTM=5
            )
    
    def test_invalid_otm_negative(self):
        """Test with negative no_of_OTM"""
        with pytest.raises(ValidationError):
            process_option_chain_with_analysis(
                symbol='NIFTY',
                exchange='NSE',
                expiry_date='nearest',
                no_of_ITM=5,
                no_of_OTM=-5
            )
    
    def test_invalid_itm_too_high(self):
        """Test with no_of_ITM exceeding limit"""
        with pytest.raises(ValidationError):
            process_option_chain_with_analysis(
                symbol='NIFTY',
                exchange='NSE',
                expiry_date='nearest',
                no_of_ITM=25,
                no_of_OTM=5
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
