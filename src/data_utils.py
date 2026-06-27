"""
data_utils.py

Functions for pulling TSLA price data and computing the technical
indicators the strategy depends on (trend SMA, fast/slow EMA, RSI, ATR,
and a rolling volume average).

All indicators are computed with rolling/ewm windows, which only ever
look backward, so there's no look-ahead leakage built in here. The
backtest engine is responsible for lagging signals by one day before
acting on them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Download daily OHLCV data for a single ticker from Yahoo Finance.

    Returns a DataFrame indexed by date with lowercase columns:
    open, high, low, close, volume.
    """
    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if raw.empty:
        raise ValueError(f"No data returned for {ticker} between {start} and {end}.")

    # yfinance sometimes returns a MultiIndex column structure even for a
    # single ticker depending on version. Flatten it if so.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
    df.index.name = "date"
    return df


def _wilder_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Classic Wilder RSI, computed with an exponential (alpha=1/window) average
    of gains and losses, which is the standard definition (not a simple SMA)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_loss != 0, 100.0)  # no losses in window -> RSI 100
    return rsi


def _wilder_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range using Wilder's smoothing."""
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    return atr


def add_indicators(
    df: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
    trend_window: int = 150,
    rsi_window: int = 14,
    atr_window: int = 14,
    volume_window: int = 20,
) -> pd.DataFrame:
    """
    Append all indicator columns the strategy needs to a price DataFrame.

    Adds: ema_fast, ema_slow, sma_trend, rsi, atr, volume_avg
    """
    out = df.copy()
    out["ema_fast"] = out["close"].ewm(span=fast_window, adjust=False).mean()
    out["ema_slow"] = out["close"].ewm(span=slow_window, adjust=False).mean()
    out["sma_trend"] = out["close"].rolling(trend_window).mean()
    out["rsi"] = _wilder_rsi(out["close"], rsi_window)
    out["atr"] = _wilder_atr(out, atr_window)
    out["volume_avg"] = out["volume"].rolling(volume_window).mean()
    return out
