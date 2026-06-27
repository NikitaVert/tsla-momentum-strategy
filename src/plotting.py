"""
plotting.py

Charting helpers used in notebook 3. Kept separate from metrics.py so
that module can be imported/tested without a display backend.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curves(equity_curve: pd.DataFrame, title: str = "Strategy vs. Buy & Hold (TSLA)"):
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(equity_curve.index, equity_curve["equity"], label="Strategy", linewidth=1.6)
    ax.plot(
        equity_curve.index,
        equity_curve["buy_hold_equity"],
        label="Buy & Hold TSLA",
        linewidth=1.6,
        linestyle="--",
    )
    ax.set_title(title)
    ax.set_ylabel("Equity ($)")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_drawdown(equity_curve: pd.DataFrame, equity_col: str = "equity"):
    equity = equity_curve[equity_col]
    drawdown = equity / equity.cummax() - 1.0

    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.fill_between(equity_curve.index, drawdown, 0, color="firebrick", alpha=0.5)
    ax.set_title("Strategy Drawdown")
    ax.set_ylabel("Drawdown")
    fig.tight_layout()
    return fig


def plot_trades_on_price(df: pd.DataFrame, trade_log: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df.index, df["close"], color="steelblue", linewidth=1.0, label="TSLA Close")

    entries = trade_log.dropna(subset=["entry_date"])
    exits = trade_log.dropna(subset=["exit_date"])

    ax.scatter(entries["entry_date"], entries["entry_price"], marker="^", color="green", s=60, label="Entry", zorder=3)
    ax.scatter(exits["exit_date"], exits["exit_price"], marker="v", color="red", s=60, label="Exit", zorder=3)

    ax.set_title("TSLA Price with Strategy Entries / Exits")
    ax.legend()
    fig.tight_layout()
    return fig
