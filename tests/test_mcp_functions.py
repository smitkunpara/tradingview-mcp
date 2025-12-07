"""
Comprehensive pytest tests for TradingView MCP server functions.
Tests use real data from actual API calls - no mocking.
"""

import pytest
import os
import sys
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from tradingview_mcp.main import (
    get_historical_data as _get_historical_data,
    get_news_headlines as _get_news_headlines,
    get_news_content as _get_news_content,
    get_all_indicators as _get_all_indicators,
    get_ideas as _get_ideas,
    get_option_chain_greeks as _get_option_chain_greeks
)

# Extract the actual callable functions from FunctionTool objects
get_historical_data = _get_historical_data.fn
get_news_headlines = _get_news_headlines.fn
get_news_content = _get_news_content.fn
get_all_indicators = _get_all_indicators.fn
get_ideas = _get_ideas.fn
get_option_chain_greeks = _get_option_chain_greeks.fn


class TestGetHistoricalData:
    """Test suite for get_historical_data function with different combinations"""
    
    def test_historical_data_nifty_no_indicators(self):
        """Test fetching NIFTY data without indicators"""
        result = get_historical_data(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1m",
            numb_price_candles=10
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_historical_data_nifty_single_indicator(self):
        """Test fetching NIFTY data with RSI indicator"""
        result = get_historical_data(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1m",
            numb_price_candles=10,
            indicators=["RSI"]
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_historical_data_nifty_multiple_indicators(self):
        """Test fetching NIFTY data with RSI and MACD indicators"""
        result = get_historical_data(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1m",
            numb_price_candles=10,
            indicators=["RSI", "MACD"]
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_historical_data_aapl_5m(self):
        """Test fetching AAPL data on NASDAQ with 5m timeframe"""
        result = get_historical_data(
            exchange="NASDAQ",
            symbol="AAPL",
            timeframe="5m",
            numb_price_candles=10
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_historical_data_btc_1h_with_rsi(self):
        """Test fetching BTC data on BINANCE with 1h timeframe and RSI"""
        result = get_historical_data(
            exchange="BINANCE",
            symbol="BTCUSDT",
            timeframe="1h",
            numb_price_candles=10,
            indicators=["RSI"]
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_historical_data_different_timeframes(self):
        """Test fetching data with different timeframes"""
        timeframes = ["1m", "5m", "15m", "1h", "1d"]
        
        for tf in timeframes:
            result = get_historical_data(
                exchange="NSE",
                symbol="NIFTY",
                timeframe=tf,
                numb_price_candles=5
            )
            assert result is not None
            print(f"Timeframe {tf} - Result: {result}")


class TestGetNewsHeadlines:
    """Test suite for get_news_headlines function"""
    
    def test_news_headlines_nifty_basic(self):
        """Test fetching news headlines for NIFTY"""
        result = get_news_headlines(
            symbol="NIFTY",
            exchange="NSE"
        )
        
        assert result is not None
        result_str = str(result)
        assert "headlines" in result_str.lower() or "success" in result_str.lower()
        print(f"Result: {result}")
    
    def test_news_headlines_nifty_with_filters(self):
        """Test fetching NIFTY news with area and provider filters"""
        result = get_news_headlines(
            symbol="NIFTY",
            exchange="NSE",
            area="asia",
            provider="all"
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_news_headlines_crypto(self):
        """Test fetching crypto news (BTC)"""
        result = get_news_headlines(
            symbol="BTC",
            exchange="BINANCE",
            area="world",
            provider="coindesk"
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_news_headlines_aapl(self):
        """Test fetching AAPL news"""
        result = get_news_headlines(
            symbol="AAPL",
            exchange="NASDAQ"
        )
        
        assert result is not None
        print(f"Result: {result}")


class TestNewsContent:
    """Test suite for get_news_content function"""
    
    def test_news_content_fetch(self):
        """Test fetching full news content using story paths from headlines"""
        # Use real story paths from earlier test results
        story_paths = [
            "/news/reuters.com,2025:newsml_L4N3XB0V8:0-india-stocks-rupee-swaps-call-at-close/",
            "/news/reuters.com,2025:newsml_L4N3XB0SQ:0-india-stocks-rupee-swaps-call-at-3-30-p-m-ist/"
        ]
        
        # Fetch content for these stories
        result = get_news_content(
            story_paths=story_paths
        )
        
        assert result is not None
        print(f"News Content Result: {result}")


class TestGetAllIndicators:
    """Test suite for get_all_indicators function"""
    
    def test_all_indicators_nifty_1m(self):
        """Test getting all indicators for NIFTY on 1m timeframe"""
        result = get_all_indicators(
            symbol="NIFTY",
            exchange="NSE",
            timeframe="1m"
        )
        
        assert result is not None
        result_str = str(result)
        assert "success" in result_str.lower() or "data" in result_str.lower()
        # Should contain RSI, MACD, or other indicators
        assert any(indicator in result_str for indicator in ["RSI", "MACD", "ADX", "EMA"])
        print(f"Result: {result}")
    
    def test_all_indicators_aapl_5m(self):
        """Test getting all indicators for AAPL on 5m timeframe"""
        result = get_all_indicators(
            symbol="AAPL",
            exchange="NASDAQ",
            timeframe="5m"
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_all_indicators_btc_1h(self):
        """Test getting all indicators for BTC on 1h timeframe"""
        result = get_all_indicators(
            symbol="BTCUSDT",
            exchange="BINANCE",
            timeframe="1h"
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_all_indicators_different_timeframes(self):
        """Test getting indicators for different timeframes"""
        timeframes = ["1m", "5m", "15m", "1h", "1d"]
        
        for tf in timeframes:
            result = get_all_indicators(
                symbol="NIFTY",
                exchange="NSE",
                timeframe=tf
            )
            assert result is not None
            print(f"Timeframe {tf} - Result: {result}")


class TestGetIdeas:
    """Test suite for get_ideas function"""
    
    def test_ideas_nifty_popular(self):
        """Test getting popular trading ideas for NIFTY"""
        result = get_ideas(
            symbol="NIFTY",
            sort="popular"
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_ideas_aapl_recent(self):
        """Test getting recent trading ideas for AAPL"""
        result = get_ideas(
            symbol="AAPL",
            sort="recent",
            startPage=1,
            endPage=2
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_ideas_btc_popular(self):
        """Test getting popular trading ideas for BTC"""
        result = get_ideas(
            symbol="BTC",
            sort="popular"
        )
        
        assert result is not None
        print(f"Result: {result}")


class TestGetOptionChainGreeks:
    """Test suite for get_option_chain_greeks function"""
    
    def test_option_chain_nifty_latest_expiry(self):
        """Test getting option chain for NIFTY with latest expiry"""
        result = get_option_chain_greeks(
            symbol="NIFTY",
            exchange="NSE",
            expiry_date="latest"
        )
        
        assert result is not None
        result_str = str(result)
        assert "success" in result_str.lower()
        print(f"Result: {result}")
    
    def test_option_chain_nifty_all_expiries(self):
        """Test getting option chain for NIFTY with all expiries"""
        result = get_option_chain_greeks(
            symbol="NIFTY",
            exchange="NSE",
            expiry_date=None,
            top_n=5
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_option_chain_banknifty_latest(self):
        """Test getting option chain for BANKNIFTY with specific top_n"""
        result = get_option_chain_greeks(
            symbol="BANKNIFTY",
            exchange="NSE",
            expiry_date="latest",
            top_n=5
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_option_chain_nifty_specific_expiry(self):
        """Test getting option chain for NIFTY with specific expiry date"""
        result = get_option_chain_greeks(
            symbol="NIFTY",
            exchange="NSE",
            expiry_date=20251202,
            top_n=3
        )
        
        assert result is not None
        print(f"Result: {result}")
    
    def test_option_chain_no_data_available(self):
        """Test option chain for stock with no options (should show error)"""
        result = get_option_chain_greeks(
            symbol="NIFTY",
            exchange="NSE",
            expiry_date=20251202
        )
        
        assert result is not None
        # Should indicate no data available or show error
        print(f"Result: {result}")
    
    def test_option_chain_different_top_n(self):
        """Test option chain with different top_n values"""
        for top_n in [1, 3, 5, 10]:
            result = get_option_chain_greeks(
                symbol="NIFTY",
                exchange="NSE",
                expiry_date="latest",
                top_n=top_n
            )
            assert result is not None
            print(f"top_n={top_n} - Result: {result}")


class TestCombinedScenarios:
    """Test combined real-world scenarios"""
    
    def test_complete_analysis_workflow(self):
        """Test complete workflow: get indicators, historical data, and option chain"""
        # 1. Get current indicators
        indicators_result = get_all_indicators(
            symbol="NIFTY",
            exchange="NSE",
            timeframe="1h"
        )
        print(f"1. Indicators: {indicators_result}")
        assert indicators_result is not None
        
        # 2. Get historical data
        historical_result = get_historical_data(
            exchange="NSE",
            symbol="NIFTY",
            timeframe="1h",
            numb_price_candles=20
        )
        print(f"2. Historical Data: {historical_result}")
        assert historical_result is not None
        
        # 3. Get option chain
        options_result = get_option_chain_greeks(
            symbol="NIFTY",
            exchange="NSE",
            expiry_date="latest",
            top_n=3
        )
        print(f"3. Option Chain: {options_result}")
        assert options_result is not None
    
    def test_news_and_ideas_workflow(self):
        """Test workflow: get news headlines, fetch content, and get ideas"""
        # 1. Get news headlines
        headlines_result = get_news_headlines(
            symbol="NIFTY",
            exchange="NSE",
            area="asia"
        )
        print(f"1. Headlines: {headlines_result}")
        assert headlines_result is not None
        
        # 2. Get trading ideas
        ideas_result = get_ideas(
            symbol="NIFTY",
            sort="popular"
        )
        print(f"2. Ideas: {ideas_result}")
        assert ideas_result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
