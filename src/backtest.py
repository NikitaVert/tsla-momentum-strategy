"""
backtest.py

An event-driven, single-asset backtest engine for the TSLA momentum
strategy. It is long/flat only (no shorting in this version -- see the
write-up for why that's a deliberate scope decision, not an oversight).

Design choices that matter for realism:
- Signals are read from yesterday's close, but trades execute at
  today's open (no same-bar look-ahead).
- Position size is volatility-scaled: each trade risks a fixed
  percentage of capital, sized off the distance to the ATR-based stop,
  rather than always going all-in. This matters more for a single
  stock than it did for the diversified ETF basket, since there's no
  cross-asset diversification to lean on.
- Shares are whole numbers; leftover cash is tracked explicitly.
- Commission and slippage are modeled, even if simplistically.
- A stop-loss is checked against the day's low, not just the close, so
  intraday stop hits aren't silently ignored.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    stop_price: float
    exit_date: pd.Timestamp | None = None
    exit_price: float | None = None
    exit_reason: str | None = None

    @property
    def pnl(self) -> float | None:
        if self.exit_price is None:
            return None
        return (self.exit_price - self.entry_price) * self.shares

    @property
    def return_pct(self) -> float | None:
        if self.exit_price is None:
            return None
        return (self.exit_price / self.entry_price) - 1.0

    @property
    def holding_days(self) -> int | None:
        if self.exit_date is None:
            return None
        return (self.exit_date - self.entry_date).days


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    risk_pct: float = 0.01,
    atr_multiplier: float = 2.5,
    commission_per_share: float = 0.005,
    slippage_bps: float = 5.0,
) -> tuple[pd.DataFrame, list[Trade]]:
    """
    Run the long/flat backtest.

    df must already contain: open, high, low, close, volume, atr,
    raw_entry, raw_exit (see data_utils.add_indicators and
    signals.generate_signals).

    Returns
    -------
    equity_curve : DataFrame indexed by date with columns
        ['cash', 'shares', 'position_value', 'equity', 'buy_hold_equity']
    trades : list[Trade]
        Closed (and, if still open at the end, one open) trade records.
    """
    slip = slippage_bps / 10_000.0

    cash = initial_capital
    shares = 0
    in_position = False
    open_trade: Trade | None = None
    trades: list[Trade] = []

    # Buy-and-hold benchmark: buy as many shares as possible on day 0's open,
    # hold to the end, same commission convention applied once.
    bh_shares = math.floor(initial_capital / (df["open"].iloc[0] * (1 + slip)))
    bh_cost = bh_shares * df["open"].iloc[0] * (1 + slip) + bh_shares * commission_per_share
    bh_cash = initial_capital - bh_cost

    records = []

    for i in range(1, len(df)):
        yesterday = df.iloc[i - 1]
        today = df.iloc[i]
        today_date = df.index[i]

        # --- Act on yesterday's close-based signal, at today's open ---
        if not in_position and bool(yesterday["raw_entry"]):
            entry_price = today["open"] * (1 + slip)
            stop_price = entry_price - atr_multiplier * yesterday["atr"]
            risk_amount = cash * risk_pct
            per_share_risk = entry_price - stop_price

            if per_share_risk > 0:
                target_shares = math.floor(risk_amount / per_share_risk)
                affordable_shares = math.floor(cash / (entry_price + commission_per_share))
                trade_shares = max(0, min(target_shares, affordable_shares))
            else:
                trade_shares = 0

            if trade_shares > 0:
                cost = trade_shares * entry_price + trade_shares * commission_per_share
                cash -= cost
                shares = trade_shares
                in_position = True
                open_trade = Trade(
                    entry_date=today_date,
                    entry_price=entry_price,
                    shares=trade_shares,
                    stop_price=stop_price,
                )

        elif in_position:
            stop_hit = today["low"] <= open_trade.stop_price
            signal_exit = bool(yesterday["raw_exit"])

            if stop_hit or signal_exit:
                # If the stop was gapped through, you get the worse of the
                # open or the stop level -- you can't assume a fill exactly
                # at the stop price if the market opens below it.
                if stop_hit:
                    exit_price = min(today["open"], open_trade.stop_price) * (1 - slip)
                    reason = "stop_loss"
                else:
                    exit_price = today["open"] * (1 - slip)
                    reason = "signal_exit"

                proceeds = shares * exit_price - shares * commission_per_share
                cash += proceeds

                open_trade.exit_date = today_date
                open_trade.exit_price = exit_price
                open_trade.exit_reason = reason
                trades.append(open_trade)

                shares = 0
                in_position = False
                open_trade = None

        position_value = shares * today["close"]
        equity = cash + position_value
        bh_equity = bh_cash + bh_shares * today["close"]

        records.append(
            {
                "date": today_date,
                "cash": cash,
                "shares": shares,
                "position_value": position_value,
                "equity": equity,
                "buy_hold_equity": bh_equity,
            }
        )

    # Close out any still-open position at the final bar's close, marked
    # as 'end_of_data' so it's not confused with a genuine strategy exit.
    if open_trade is not None:
        last_date = df.index[-1]
        last_close = df["close"].iloc[-1]
        open_trade.exit_date = last_date
        open_trade.exit_price = last_close * (1 - slip)
        open_trade.exit_reason = "end_of_data"
        trades.append(open_trade)

    equity_curve = pd.DataFrame(records).set_index("date")
    return equity_curve, trades


def trades_to_frame(trades: list[Trade]) -> pd.DataFrame:
    """Convert the list of Trade objects into a flat DataFrame for analysis."""
    rows = [
        {
            "entry_date": t.entry_date,
            "exit_date": t.exit_date,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "shares": t.shares,
            "pnl": t.pnl,
            "return_pct": t.return_pct,
            "holding_days": t.holding_days,
            "exit_reason": t.exit_reason,
        }
        for t in trades
    ]
    return pd.DataFrame(rows)
