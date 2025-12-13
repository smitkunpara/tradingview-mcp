"""
Real tests for fetch_minds function.
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

from tradingview_mcp.tradingview_tools import fetch_minds
from tradingview_mcp.validators import ValidationError


class TestFetchMinds:
    """Test fetch_minds with real data"""
    
    def test_basic_minds_fetch(self):
        """Test fetching minds discussions"""
        result = fetch_minds(
            symbol='NIFTY',
            exchange='NSE',
            limit=10
        )
        
        assert result['success'] == True
        assert 'data' in result
        assert isinstance(result['data'], list)
    
    def test_minds_with_no_limit(self):
        """Test with default limit (None)"""
        result = fetch_minds(
            symbol='AAPL',
            exchange='NASDAQ',
            limit=None
        )
        
        assert result['success'] == True
        assert isinstance(result['data'], list)
    
    def test_minds_different_symbols(self):
        """Test with different symbols"""
        symbols = [
            ('NIFTY', 'NSE'),
            ('BTCUSD', 'BINANCE'),
            ('AAPL', 'NASDAQ')
        ]
        
        for symbol, exchange in symbols:
            result = fetch_minds(
                symbol=symbol,
                exchange=exchange,
                limit=5
            )
            
            assert result['success'] == True
            print(f"✓ {symbol} on {exchange} works")
    
    def test_minds_with_limit(self):
        """Test with specific limit"""
        result = fetch_minds(
            symbol='ETHUSDT',
            exchange='BINANCE',
            limit=15
        )
        
        assert result['success'] == True
        assert isinstance(result['data'], list)
    
    def test_invalid_exchange(self):
        """Test with invalid exchange"""
        with pytest.raises(ValidationError):
            fetch_minds(
                symbol='NIFTY',
                exchange='INVALID_EXCHANGE',
                limit=10
            )
    
    def test_invalid_limit_negative(self):
        """Test with negative limit"""
        with pytest.raises(ValidationError):
            fetch_minds(
                symbol='NIFTY',
                exchange='NSE',
                limit=-5
            )
    
    def test_invalid_limit_zero(self):
        """Test with zero limit"""
        with pytest.raises(ValidationError):
            fetch_minds(
                symbol='NIFTY',
                exchange='NSE',
                limit=0
            )
    
    def test_minds_data_structure(self):
        """Test minds data structure"""
        result = fetch_minds(
            symbol='NIFTY',
            exchange='NSE',
            limit=5
        )
        
        assert result['success'] == True
        assert 'data' in result
        
        # If data is present, check structure
        if len(result['data']) > 0:
            mind = result['data'][0]
            assert isinstance(mind, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
