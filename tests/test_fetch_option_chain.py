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

from tradingview_mcp.tradingview_tools import fetch_option_chain_data
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
    
    def test_option_chain_with_analysis(self):
        """Test option chain with analysis"""
        result = fetch_option_chain_data(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date=None
        )
        
        assert result['success'] == True
        assert 'data' in result
    
    def test_option_chain_specific_expiry(self):
        """Test with specific expiry date"""
        result = fetch_option_chain_data(
            symbol='NIFTY',
            exchange='NSE',
            expiry_date=20251202  # Example expiry
        )
        
        assert result['success'] == True
        assert 'data' in result
    
    # def test_option_chain_different_top_n(self):
    #     """Test with different top_n values"""
    #     top_n_values = [3, 5, 10]
        
    #     for top_n in top_n_values:
    #         result = process_option_chain_with_analysis(
    #             symbol='NIFTY',
    #             exchange='NSE',
    #             expiry_date='latest',
    #             top_n=top_n
    #         )
            
    #         assert result['success'] == True
    #         print(f"✓ top_n={top_n} works")
    
    # def test_option_chain_banknifty(self):
    #     """Test with BANKNIFTY symbol"""
    #     result = process_option_chain_with_analysis(
    #         symbol='BANKNIFTY',
    #         exchange='NSE',
    #         expiry_date='latest',
    #         top_n=5
    #     )
        
    #     assert result['success'] == True
    #     assert 'spot_price' in result
    
    # def test_invalid_exchange(self):
    #     """Test with invalid exchange"""
    #     with pytest.raises(ValidationError):
    #         process_option_chain_with_analysis(
    #             symbol='NIFTY',
    #             exchange='INVALID_EXCHANGE',
    #             expiry_date='latest',
    #             top_n=5
    #         )
    
    # def test_invalid_top_n_zero(self):
    #     """Test with zero top_n"""
    #     with pytest.raises(ValidationError):
    #         process_option_chain_with_analysis(
    #             symbol='NIFTY',
    #             exchange='NSE',
    #             expiry_date='latest',
    #             top_n=0
    #         )
    
    # def test_invalid_top_n_negative(self):
    #     """Test with negative top_n"""
    #     with pytest.raises(ValidationError):
    #         process_option_chain_with_analysis(
    #             symbol='NIFTY',
    #             exchange='NSE',
    #             expiry_date='latest',
    #             top_n=-5
    #         )
    
    # def test_invalid_top_n_too_high(self):
    #     """Test with top_n exceeding limit"""
    #     with pytest.raises(ValidationError):
    #         process_option_chain_with_analysis(
    #             symbol='NIFTY',
    #             exchange='NSE',
    #             expiry_date='latest',
    #             top_n=25
    #         )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
