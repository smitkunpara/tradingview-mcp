"""
Real tests for fetch_news_headlines function.
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

from tradingview_mcp.tradingview_tools import fetch_news_headlines
from tradingview_mcp.validators import ValidationError


class TestFetchNewsHeadlines:
    """Test fetch_news_headlines with real data"""
    
    def test_basic_news_fetch(self):
        """Test fetching news headlines"""
        result = fetch_news_headlines(
            symbol='AAPL',
            exchange='NASDAQ',
            provider='all',
            area='americas'
        )
        
        assert isinstance(result, list)
        if len(result) > 0:
            headline = result[0]
            assert 'title' in headline
            assert 'storyPath' in headline or 'url' in headline
    
    def test_news_different_providers(self):
        """Test with different news providers"""
        providers = ['all', 'dow-jones', 'tradingview']
        
        for provider in providers:
            result = fetch_news_headlines(
                symbol='BTCUSD',
                exchange='BITSTAMP',
                provider=provider,
                area='world'
            )
            
            assert isinstance(result, list)
            print(f"✓ Provider {provider} works")
    
    def test_news_different_areas(self):
        """Test with different geographical areas"""
        areas = ['world', 'americas', 'europe', 'asia']
        
        for area in areas:
            result = fetch_news_headlines(
                symbol='NIFTY',
                exchange='NSE',
                provider='all',
                area=area
            )
            
            assert isinstance(result, list)
            print(f"✓ Area {area} works")
    
    def test_news_without_exchange(self):
        """Test without specifying exchange - should use default behavior"""
        # Exchange is now required for the fetch to work properly
        # This test is skipped as the API requires exchange
        pytest.skip("Exchange is required for news headlines")
    
    def test_news_crypto_symbols(self):
        """Test with crypto symbols"""
        result = fetch_news_headlines(
            symbol='ETHUSDT',
            exchange='BINANCE',
            provider='all',
            area='world'
        )
        
        assert isinstance(result, list)
    
    def test_news_stock_symbols(self):
        """Test with stock symbols"""
        result = fetch_news_headlines(
            symbol='TSLA',
            exchange='NASDAQ',
            provider='all',
            area='americas'
        )
        
        assert isinstance(result, list)
    
    def test_invalid_area(self):
        """Test with invalid area"""
        with pytest.raises(ValidationError):
            fetch_news_headlines(
                symbol='AAPL',
                exchange='NASDAQ',
                provider='all',
                area='invalid_area'
            )
    
    def test_invalid_exchange(self):
        """Test with invalid exchange"""
        with pytest.raises(ValidationError):
            fetch_news_headlines(
                symbol='AAPL',
                exchange='INVALID_EXCHANGE',
                provider='all',
                area='americas'
            )
    
    def test_news_headline_structure(self):
        """Test that headlines have correct structure"""
        result = fetch_news_headlines(
            symbol='AAPL',
            exchange='NASDAQ',
            provider='all',
            area='americas'
        )
        
        if len(result) > 0:
            headline = result[0]
            
            # Check for required fields
            assert 'title' in headline
            # storyPath or url should be present
            assert 'storyPath' in headline or 'url' in headline or 'link' in headline


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
