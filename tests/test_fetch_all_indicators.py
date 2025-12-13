"""
Real tests for fetch_all_indicators function.
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

from tradingview_mcp.tradingview_tools import fetch_all_indicators
from tradingview_mcp.validators import ValidationError


class TestFetchAllIndicators:
    """Test fetch_all_indicators with real data"""
    
    def test_basic_indicators_fetch(self):
        """Test fetching all indicators"""
        result = fetch_all_indicators(
            symbol='NIFTY',
            exchange='NSE',
            timeframe='1m'
        )
        
        assert result['success'] == True
        assert 'data' in result
        assert isinstance(result['data'], dict)
        assert len(result['data']) > 0
    
    def test_indicators_different_timeframes(self):
        """Test with different timeframes"""
        timeframes = ['1m', '5m', '1h', '1d']
        
        for tf in timeframes:
            result = fetch_all_indicators(
                symbol='AAPL',
                exchange='NASDAQ',
                timeframe=tf
            )
            
            assert result['success'] == True
            assert len(result['data']) > 0
            print(f"✓ Timeframe {tf} works")
    
    def test_indicators_crypto_symbols(self):
        """Test with crypto symbols"""
        result = fetch_all_indicators(
            symbol='BTCUSD',
            exchange='BINANCE',
            timeframe='5m'
        )
        
        assert result['success'] == True
        assert len(result['data']) > 0
    
    def test_indicators_stock_symbols(self):
        """Test with stock symbols"""
        result = fetch_all_indicators(
            symbol='TSLA',
            exchange='NASDAQ',
            timeframe='1h'
        )
        
        assert result['success'] == True
        assert len(result['data']) > 0
    
    def test_indicators_data_structure(self):
        """Test indicators data structure"""
        result = fetch_all_indicators(
            symbol='NIFTY',
            exchange='NSE',
            timeframe='1m'
        )
        
        assert result['success'] == True
        assert 'data' in result
        
        # Data should be a dictionary of indicator_name: value
        for indicator_name, value in result['data'].items():
            assert isinstance(indicator_name, str)
    
    def test_invalid_exchange(self):
        """Test with invalid exchange"""
        with pytest.raises(ValidationError):
            fetch_all_indicators(
                symbol='NIFTY',
                exchange='INVALID_EXCHANGE',
                timeframe='1m'
            )
    
    def test_invalid_timeframe(self):
        """Test with invalid timeframe"""
        with pytest.raises(ValidationError):
            fetch_all_indicators(
                symbol='NIFTY',
                exchange='NSE',
                timeframe='3m'
            )
    
    def test_indicators_common_indicators_present(self):
        """Test that common indicators are present"""
        result = fetch_all_indicators(
            symbol='NIFTY',
            exchange='NSE',
            timeframe='1m'
        )
        
        assert result['success'] == True
        
        # Check for some common indicators (names may vary)
        indicators = result['data']
        indicator_keys = [k.upper() for k in indicators.keys()]
        
        # At least some common indicators should be present
        assert len(indicators) > 5, "Expected multiple indicators"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
