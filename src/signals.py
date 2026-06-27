"""
signals.py

Pure signal logic: given a DataFrame that already has the indicator
columns from data_utils.add_indicators, decide on each day whether
conditions support being long ("regime"), whether today is a fresh
entry trigger, and whether today is an exit trigger.

This module is deliberately stateless -- it does not know about
positions, cash, or stops. That state-dependent logic (you can't enter
if you're already in a trade, stop-loss tracking, position sizing,
etc.) lives in backtest.py. Keeping signal logic separate from
execution logic makes each piece easier to test and reason about on
its own.

Important: these conditions are based only on information available as
of that day's close, so the backtest engine must act on them using the
*next* day's open to avoid look-ahead bias.
"""

from __future__ import annotations

import pandas as pd


def generate_signals(
    df: pd.DataFrame,
    rsi_low: float = 50.0,
    rsi_high: float = 75.0,
    require_volume_confirmation: bool = True,
) -> pd.DataFrame:
    """
    Add 'regime', 'raw_entry', and 'raw_exit' boolean columns.

    regime:    price above the long trend SMA -> long-only environment
    raw_entry: fast EMA crosses above slow EMA, *and* we're in the bullish
               regime, *and* RSI is in the [rsi_low, rsi_high] momentum band,
               *and* (optionally) volume confirms conviction
    raw_exit:  fast EMA crosses below slow EMA, OR price drops out of regime
               (closes back below the trend SMA)

    These are "would-like-to-be-long" / "would-like-to-exit" flags for that
    day's close. The backtest engine lags them by one day before trading.
    """
    out = df.copy()

    out["regime"] = out["close"] > out["sma_trend"]

    ema_cross_up = (out["ema_fast"] > out["ema_slow"]) & (
        out["ema_fast"].shift(1) <= out["ema_slow"].shift(1)
    )
    ema_cross_down = (out["ema_fast"] < out["ema_slow"]) & (
        out["ema_fast"].shift(1) >= out["ema_slow"].shift(1)
    )

    rsi_ok = (out["rsi"] >= rsi_low) & (out["rsi"] <= rsi_high)

    if require_volume_confirmation:
        volume_ok = out["volume"] > out["volume_avg"]
    else:
        volume_ok = True

    out["raw_entry"] = ema_cross_up & out["regime"] & rsi_ok & volume_ok
    out["raw_exit"] = ema_cross_down | (~out["regime"])

    return out
