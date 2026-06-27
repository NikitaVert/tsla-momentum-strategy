# TSLA Momentum Trading Model

A long/flat momentum strategy for Tesla (TSLA), combining a trend filter, an
EMA crossover trigger, an RSI momentum band, and a volume confirmation
check, backtested with realistic execution assumptions (next-day-open
fills, commissions, slippage, volatility-scaled position sizing, and an
ATR-based stop-loss).

## Repo structure

```
.
├── README.md
├── requirements.txt
├── src/
│   ├── data_utils.py     # price data fetch + indicator calculation
│   ├── signals.py        # entry/exit signal logic
│   ├── backtest.py        # event-driven backtest engine
│   ├── metrics.py         # portfolio-level and trade-level performance metrics
│   └── plotting.py        # chart helpers
├── notebooks/
│   ├── 01_data_and_signals.ipynb         # pull data, compute indicators, build signals
│   ├── 02_backtest.ipynb                 # run the backtest engine
│   └── 03_performance_and_validation.ipynb  # metrics, charts, in-sample/out-of-sample check
└── writeup/
    └── TSLA_Momentum_Writeup.md
```

## How to run

1. `pip install -r requirements.txt`
2. Run the notebooks in order: `01` → `02` → `03`. Each notebook saves its
   output to a pickle file that the next notebook loads, mirroring a clean
   separation between signal generation, simulation, and analysis.
3. Google Colab works fine for this — just upload the `src/` folder
   alongside the notebooks (or `pip install` from the repo) so the imports
   resolve.

## Methodology summary

- **Trend regime:** price above its 150-day SMA defines a long-permitted regime.
- **Entry trigger:** 20-day EMA crosses above the 50-day EMA, while in the
  bullish regime, RSI(14) is between 50–75 (momentum present, not yet
  overextended), and volume is above its 20-day average.
- **Exit:** EMA cross-under, a close back below the trend SMA, or a
  2.5×ATR(14) stop-loss — whichever happens first.
- **Position sizing:** each trade risks a fixed 1% of current cash, sized by
  distance from entry to the stop, rather than always going all-in.
- **Execution realism:** signals are read off yesterday's close and executed
  at today's open; commissions ($0.005/share) and slippage (5 bps) are
  applied; stops are checked against the day's low, not just the close.

Full rationale, results, and limitations are in
[`writeup/TSLA_Momentum_Writeup.md`](writeup/TSLA_Momentum_Writeup.md).

## A note on scope

This is a long/flat-only model — it doesn't take short positions in
downtrends, and it trades on daily bars rather than intraday. Both are
deliberate scope decisions given the timeline, not oversights; they're
discussed as next steps in the write-up.
