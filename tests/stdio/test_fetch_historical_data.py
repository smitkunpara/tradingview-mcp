"""
Real tests for fetch_historical_data function.
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

from tradingview_mcp.tradingview_tools import fetch_historical_data
from tradingview_mcp.validators import ValidationError


class TestFetchHistoricalData:
    """Test fetch_historical_data with real data"""
    
    def test_basic_ohlc_without_indicators(self):
        """Test fetching basic OHLC data without indicators"""
        result = fetch_historical_data(
            symbol='NIFTY',
            exchange='NSE',
            timeframe='1m',
            numb_price_candles=10,
            indicators=[]
        )
        
        assert result['success'] == True
        assert 'data' in result
        assert len(result['data']) > 0
        
        # Check OHLC structure
        first_candle = result['data'][0]
        assert 'open' in first_candle
        assert 'high' in first_candle
        assert 'low' in first_candle
        assert 'close' in first_candle
        assert 'volume' in first_candle
        assert 'datetime_ist' in first_candle or 'timestamp' in first_candle
    
    def test_ohlc_with_single_indicator(self):
        """Test with single indicator (RSI)"""
        result = fetch_historical_data(
            symbol='BTCUSD',
            exchange='BINANCE',
            timeframe='5m',
            numb_price_candles=20,
            indicators=['RSI']
        )
        
        assert result['success'] == True
        assert len(result['data']) > 0
        
        # Check if RSI is present (could be 'RSI', 'RSI@14', or 'Relative_Strength_Index')
        first_candle = result['data'][0]
        has_rsi = any('RSI' in key or 'Relative_Strength_Index' in key for key in first_candle.keys())
        assert has_rsi, "RSI indicator not found in data"
    
    def test_ohlc_different_timeframes(self):
        """Test with different timeframes"""
        timeframes = ['1m', '5m', '15m', '1h', '1d']
        
        for tf in timeframes:
            result = fetch_historical_data(
                symbol='AAPL',
                exchange='NASDAQ',
                timeframe=tf,
                numb_price_candles=5,
                indicators=[]
            )
            
            assert result['success'] == True
            assert len(result['data']) > 0
            print(f"✓ Timeframe {tf} works")
    
    def test_invalid_exchange(self):
        """Test with invalid exchange"""
        with pytest.raises(ValidationError):
            fetch_historical_data(
                symbol='NIFTY',
                exchange='INVALID_EXCHANGE',
                timeframe='1m',
                numb_price_candles=10,
                indicators=[]
            )
    
    def test_invalid_timeframe(self):
        """Test with invalid timeframe"""
        with pytest.raises(ValidationError):
            fetch_historical_data(
                symbol='NIFTY',
                exchange='NSE',
                timeframe='3m',
                numb_price_candles=10,
                indicators=[]
            )
    
    def test_invalid_candle_count(self):
        """Test with invalid number of candles"""
        with pytest.raises(ValidationError):
            fetch_historical_data(
                symbol='NIFTY',
                exchange='NSE',
                timeframe='1m',
                numb_price_candles=6000,  # Exceeds max
                indicators=[]
            )
    
    def test_crypto_exchange(self):
        """Test with crypto exchange"""
        result = fetch_historical_data(
            symbol='ETHUSDT',
            exchange='BINANCE',
            timeframe='1h',
            numb_price_candles=10,
            indicators=[]
        )
        
        assert result['success'] == True
        assert len(result['data']) > 0
    
    def test_stock_exchange(self):
        """Test with stock exchange"""
        result = fetch_historical_data(
            symbol='TSLA',
            exchange='NASDAQ',
            timeframe='1h',
            numb_price_candles=10,
            indicators=[]
        )
        
        assert result['success'] == True
        assert len(result['data']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
