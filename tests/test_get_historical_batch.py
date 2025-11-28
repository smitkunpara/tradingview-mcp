import os
import sys
import pathlib
import importlib

# Ensure src is on sys.path so we can import the package
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

import pytest


def fake_fetch_historical_data(exchange, symbol, timeframe, numb_price_candles, indicators):
    # Return a stable, simple payload that resembles the real function's structure
    return {
        'success': True,
        'data': [
            {'datetime_ist': '2025-10-07T00:00:00', 'open': 1, 'high': 2, 'low': 0.5, 'close': 1.5}
        ],
        'errors': [],
        'metadata': {'exchange': exchange, 'symbol': symbol, 'timeframe': timeframe}
    }


def test_get_historical_batch_happy_path(monkeypatch, tmp_path):
    # Import the module and monkeypatch its fetch_historical_data
    mainmod = importlib.import_module('tradingview_mcp.main')
    monkeypatch.setattr(mainmod, 'fetch_historical_data', fake_fetch_historical_data)

    requests = [
        {
            'symbol': 'BTCUSDT',
            'exchange': 'BINANCE',
            'request_data': [
                {'timeframe': '1m', 'numb_price_candles': 100, 'indicators': ['RSI']},
                {'timeframe': '5m', 'numb_price_candles': 200, 'indicators': []}
            ]
        },
        {
            'symbol': 'ETHUSDT',
            'exchange': 'BINANCE',
            'request_data': [
                {'timeframe': '15m', 'numb_price_candles': 150, 'indicators': ['MACD']}
            ]
        }
    ]

    # get_historical_batch is wrapped as a FunctionTool by FastMCP; call the underlying function
    resp = mainmod.get_historical_batch.fn(requests)

    assert resp.get('success') is True
    assert isinstance(resp.get('results'), list)
    assert len(resp['results']) == 2
    # check first symbol structure
    first = resp['results'][0]
    assert first['symbol'] == 'BTCUSDT'
    assert len(first['requests']) == 2
    for req in first['requests']:
        assert req['response']['success'] is True
        assert isinstance(req['response']['data'], list)


def test_get_historical_batch_with_invalid_item(monkeypatch):
    mainmod = importlib.import_module('tradingview_mcp.main')
    monkeypatch.setattr(mainmod, 'fetch_historical_data', fake_fetch_historical_data)

    # One item missing symbol, one valid item
    requests = [
        {
            # missing symbol
            'exchange': 'BINANCE',
            'request_data': [{'timeframe': '1m', 'numb_price_candles': 10}]
        },
        {
            'symbol': 'LTCUSDT',
            'exchange': 'BINANCE',
            'request_data': [{'timeframe': '1m', 'numb_price_candles': 10}]
        }
    ]

    resp = mainmod.get_historical_batch.fn(requests)

    # Overall success may still be True because function processes others
    assert 'results' in resp
    assert any(r.get('symbol') == 'LTCUSDT' for r in resp['results'])
    # There should be some errors reported for the invalid item
    assert isinstance(resp.get('errors'), list)
    assert len(resp['errors']) >= 1
