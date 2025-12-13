"""
Real tests for fetch_news_content function.
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

from tradingview_mcp.tradingview_tools import fetch_news_headlines, fetch_news_content
from tradingview_mcp.validators import ValidationError


class TestFetchNewsContent:
    """Test fetch_news_content with real data"""
    
    def test_basic_news_content_fetch(self):
        """Test fetching news content from headlines"""
        # First get headlines
        headlines = fetch_news_headlines(
            symbol='AAPL',
            exchange='NASDAQ',
            provider='all',
            area='americas'
        )
        
        if len(headlines) > 0 and 'storyPath' in headlines[0]:
            story_path = headlines[0]['storyPath']
            
            # Fetch content
            result = fetch_news_content([story_path])
            
            assert isinstance(result, list)
            assert len(result) > 0
            
            content = result[0]
            assert 'success' in content
    
    def test_news_content_single_story(self):
        """Test with single story path"""
        # Get a real story path first
        headlines = fetch_news_headlines(
            symbol='BTCUSD',
            exchange='BINANCE',
            provider='all',
            area='world'
        )
        
        if len(headlines) > 0 and 'storyPath' in headlines[0]:
            story_paths = [headlines[0]['storyPath']]
            result = fetch_news_content(story_paths)
            
            assert isinstance(result, list)
            assert len(result) == 1
    
    def test_news_content_multiple_stories(self):
        """Test with multiple story paths"""
        # Get multiple story paths
        headlines = fetch_news_headlines(
            symbol='NIFTY',
            exchange='NSE',
            provider='all',
            area='asia'
        )
        
        story_paths = [h['storyPath'] for h in headlines[:3] if 'storyPath' in h]
        
        if len(story_paths) > 0:
            result = fetch_news_content(story_paths)
            
            assert isinstance(result, list)
            assert len(result) <= len(story_paths)
    
    def test_invalid_story_path_format(self):
        """Test with invalid story path format"""
        with pytest.raises(ValidationError):
            fetch_news_content(['invalid_path'])
    
    def test_empty_story_paths(self):
        """Test with empty story paths list"""
        with pytest.raises(ValidationError):
            fetch_news_content([])
    
    def test_news_content_structure(self):
        """Test news content structure"""
        # Get headlines first
        headlines = fetch_news_headlines(
            symbol='AAPL',
            exchange='NASDAQ',
            provider='all',
            area='americas'
        )
        
        if len(headlines) > 0 and 'storyPath' in headlines[0]:
            story_path = headlines[0]['storyPath']
            result = fetch_news_content([story_path])
            
            if len(result) > 0:
                content = result[0]
                assert 'success' in content
                
                if content['success']:
                    assert 'title' in content
                    assert 'body' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
