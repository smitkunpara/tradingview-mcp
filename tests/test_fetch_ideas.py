"""
Real tests for fetch_ideas function.
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

from tradingview_mcp.tradingview_tools import fetch_ideas
from tradingview_mcp.validators import ValidationError


class TestFetchIdeas:
    """Test fetch_ideas with real data"""
    
    def test_basic_ideas_fetch(self):
        """Test fetching ideas"""
        result = fetch_ideas(
            symbol='NIFTY',
            startPage=1,
            endPage=1,
            sort='popular'
        )
        
        assert result['success'] == True
        assert 'ideas' in result
        assert isinstance(result['ideas'], list)
    
    def test_ideas_popular_sort(self):
        """Test with popular sort"""
        result = fetch_ideas(
            symbol='AAPL',
            startPage=1,
            endPage=1,
            sort='popular'
        )
        
        assert result['success'] == True
        assert len(result['ideas']) > 0
    
    def test_ideas_recent_sort(self):
        """Test with recent sort"""
        result = fetch_ideas(
            symbol='BTCUSD',
            startPage=1,
            endPage=1,
            sort='recent'
        )
        
        assert result['success'] == True
        assert isinstance(result['ideas'], list)
    
    def test_ideas_multiple_pages(self):
        """Test fetching multiple pages"""
        result = fetch_ideas(
            symbol='NIFTY',
            startPage=1,
            endPage=2,
            sort='popular'
        )
        
        assert result['success'] == True
        assert isinstance(result['ideas'], list)
    
    def test_ideas_different_symbols(self):
        """Test with different symbols"""
        symbols = ['NIFTY', 'AAPL', 'ETHUSDT']
        
        for symbol in symbols:
            result = fetch_ideas(
                symbol=symbol,
                startPage=1,
                endPage=1,
                sort='popular'
            )
            
            assert result['success'] == True
            print(f"✓ Symbol {symbol} works")
    
    def test_invalid_sort_option(self):
        """Test with invalid sort option"""
        with pytest.raises(ValidationError):
            fetch_ideas(
                symbol='NIFTY',
                startPage=1,
                endPage=1,
                sort='invalid_sort'
            )
    
    def test_invalid_page_range(self):
        """Test with invalid page range (end < start)"""
        with pytest.raises(ValidationError):
            fetch_ideas(
                symbol='NIFTY',
                startPage=3,
                endPage=1,
                sort='popular'
            )
    
    def test_invalid_start_page_type(self):
        """Test with invalid start_page type"""
        with pytest.raises(ValidationError):
            fetch_ideas(
                symbol='NIFTY',
                startPage='invalid',
                endPage=1,
                sort='popular'
            )
    
    def test_ideas_structure(self):
        """Test ideas data structure"""
        result = fetch_ideas(
            symbol='NIFTY',
            startPage=1,
            endPage=1,
            sort='popular'
        )
        
        assert result['success'] == True
        assert 'ideas' in result
        assert 'count' in result
        
        # If ideas are present, check structure
        if len(result['ideas']) > 0:
            idea = result['ideas'][0]
            assert isinstance(idea, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
