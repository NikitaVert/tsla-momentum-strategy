"""
metrics.py

Two families of metrics, matching what the task asks for:

1. Portfolio-level (computed off the daily equity curve):
   cumulative return, CAGR, annualized volatility, Sharpe ratio,
   Sortino ratio, max drawdown, and exposure (% of days in a position).

2. Trade-level (computed off the trade log):
   number of trades, win rate, profit factor, average trade return,
   average holding period, best/worst trade.

Risk-free rate is assumed to be 0 for Sharpe/Sortino, which is a
simplification worth naming explicitly in the write-up rather than
quietly baking in.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def portfolio_metrics(equity_curve: pd.DataFrame, equity_col: str = "equity") -> dict:
    equity = equity_curve[equity_col]
    daily_returns = equity.pct_change().dropna()

    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    n_years = len(equity) / TRADING_DAYS_PER_YEAR
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / n_years) - 1.0 if n_years > 0 else np.nan

    ann_vol = daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe = (
        daily_returns.mean() / daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        if daily_returns.std() > 0
        else np.nan
    )

    downside = daily_returns[daily_returns < 0]
    sortino = (
        daily_returns.mean() / downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        if len(downside) > 0 and downside.std() > 0
        else np.nan
    )

    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_drawdown = drawdown.min()

    result = {
        "total_return": total_return,
        "cagr": cagr,
        "annualized_volatility": ann_vol,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown": max_drawdown,
    }

    # Exposure (% of days actually holding a position) only makes sense for
    # the strategy's own equity curve, since "shares" isn't tracked for the
    # buy-and-hold benchmark column. Add it only when that column exists.
    if equity_col == "equity" and "shares" in equity_curve.columns:
        result["exposure_pct"] = (equity_curve["shares"] > 0).mean()

    return result


def trade_metrics(trade_log: pd.DataFrame) -> dict:
    closed = trade_log.dropna(subset=["return_pct"])

    if closed.empty:
        return {
            "num_trades": 0,
            "win_rate": np.nan,
            "profit_factor": np.nan,
            "avg_trade_return": np.nan,
            "avg_winner": np.nan,
            "avg_loser": np.nan,
            "avg_holding_days": np.nan,
            "best_trade": np.nan,
            "worst_trade": np.nan,
        }

    wins = closed[closed["pnl"] > 0]
    losses = closed[closed["pnl"] <= 0]

    gross_profit = wins["pnl"].sum()
    gross_loss = -losses["pnl"].sum()  # positive number

    return {
        "num_trades": len(closed),
        "win_rate": len(wins) / len(closed),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else np.inf,
        "avg_trade_return": closed["return_pct"].mean(),
        "avg_winner": wins["return_pct"].mean() if len(wins) > 0 else np.nan,
        "avg_loser": losses["return_pct"].mean() if len(losses) > 0 else np.nan,
        "avg_holding_days": closed["holding_days"].mean(),
        "best_trade": closed["return_pct"].max(),
        "worst_trade": closed["return_pct"].min(),
    }


def summarize(equity_curve: pd.DataFrame, trade_log: pd.DataFrame) -> pd.DataFrame:
    """Combine strategy vs. buy-and-hold portfolio metrics with trade metrics
    into one readable table for the write-up."""
    strat = portfolio_metrics(equity_curve, "equity")
    bh = portfolio_metrics(equity_curve, "buy_hold_equity")
    trades = trade_metrics(trade_log)

    rows = {
        "Total Return": [strat["total_return"], bh["total_return"]],
        "CAGR": [strat["cagr"], bh["cagr"]],
        "Annualized Volatility": [strat["annualized_volatility"], bh["annualized_volatility"]],
        "Sharpe Ratio": [strat["sharpe_ratio"], bh["sharpe_ratio"]],
        "Sortino Ratio": [strat["sortino_ratio"], bh["sortino_ratio"]],
        "Max Drawdown": [strat["max_drawdown"], bh["max_drawdown"]],
        "Exposure (% days in position)": [strat.get("exposure_pct", np.nan), 1.0],
    }
    summary = pd.DataFrame(rows, index=["Strategy", "Buy & Hold TSLA"]).T

    trade_summary = pd.Series(trades, name="Trade-Level Stats").to_frame()

    return summary, trade_summary
