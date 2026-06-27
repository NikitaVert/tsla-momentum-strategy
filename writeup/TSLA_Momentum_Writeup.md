# Momentum Trading Model for Tesla (TSLA)

## Methodology

The model is a long/flat momentum strategy that trades TSLA against its own price and volume history — there's no cross-sectional universe to rank it against, so the signal has to be built entirely from time-series (absolute) momentum rather than relative ranking.

Four conditions combine to generate an entry, each targeting a specific failure mode of a naive moving-average system:

1. **Trend regime** — price above its 150-day SMA. This keeps the strategy out of the market during sustained downtrends rather than trying to catch every short-term bounce.
2. **Momentum trigger** — the 20-day EMA crossing above the 50-day EMA, *within* the bullish regime. This times entries to the point where short-term momentum is reasserting itself, rather than entering on the regime change alone (which would be far too early or too late depending on the underlying trend's shape).
3. **RSI filter (50–75 band)** — confirms momentum is present without being already exhausted. Entries are skipped above RSI 75, where the move is more likely to be a near-term blow-off than a fresh continuation.
4. **Volume confirmation** — the signal day's volume must exceed its 20-day average, to filter out breakouts on unconvincing, low-conviction trading.

Exits trigger on an EMA cross-under, a close back below the trend SMA, or a 2.5×ATR(14) stop-loss, whichever comes first. Position size is volatility-scaled: each trade risks a fixed 1% of current capital, sized by the distance from entry to the stop, rather than committing the full account to every trade. That matters more here than it would for a diversified basket, since a single name carries idiosyncratic risk that can't be diversified away.

All parameters (EMA lengths, RSI band, trend window, ATR multiplier, risk-per-trade) were chosen *a priori*, using standard conventions, before looking at any backtest output — not fit to maximize backtest performance. This was a deliberate choice given the timeline: a classical, fully transparent model that can be reasoned about and explained end-to-end is more defensible than a more complex (ML/DL) model built quickly enough to carry real overfitting or bug risk without time to validate it properly.

Execution is modeled with next-day-open fills (a signal generated at today's close is never tradeable until tomorrow's open), $0.005/share commission, 5 bps slippage, and stops checked against the day's low rather than only the close, so an intraday stop breach isn't missed.

## Results

Backtest period: **2015-08-06 to 2025-08-29** (2,532 trading days, after the 150-day SMA warm-up window).

| Metric | Strategy | Buy & Hold TSLA |
|---|---|---|
| Total Return | 11.8% | 1,965.7% |
| CAGR | 1.1% | 35.2% |
| Annualized Volatility | 3.4% | 59.1% |
| Sharpe Ratio | 0.34 | 0.80 |
| Sortino Ratio | 0.18 | 1.19 |
| Max Drawdown | -9.3% | -73.6% |

Trade-level: **8 trades**, **25% win rate**, **3.38 profit factor**, **30.7% average trade return**, **71.6 days** average holding period. Best trade +288.4% (the April 2020 – March 2021 COVID-recovery position), worst trade -13.4%.

**In-sample vs. out-of-sample (split at 2022-01-01):**

| Metric | In-Sample (2015–2021) | Out-of-Sample (2022–2025) |
|---|---|---|
| Strategy Sharpe | 0.48 | -0.13 |
| Strategy Max Drawdown | -8.5% | -4.5% |
| Number of trades | 5 | 3 |
| Win rate | 20% | 33.3% |
| Profit factor | 5.65 | 0.56 |
| Buy & Hold Sharpe | 1.13 | 0.25 |
| Buy & Hold Max Drawdown | -60.6% | -71.7% |

The honest read of these results is mixed, and worth stating plainly rather than spinning favorably.

The strategy did what its design intends on risk: it was only in a position 22.6% of the time (573 of 2,532 trading days), which is why its volatility (3.4% vs. 59.1%) and max drawdown (-9.3% vs. -73.6%) are dramatically smaller than buy-and-hold's. That difference persists out-of-sample too — even as the strategy's edge weakened post-2022, its drawdown (-4.5%) stayed far smaller than TSLA's own (-71.7% over the same window).

Where it falls short is return, including risk-adjusted return. Buy-and-hold's Sharpe ratio beats the strategy's both over the full period (0.80 vs. 0.34) and in-sample (1.13 vs. 0.48) — the volatility reduction wasn't large enough to offset the return given up by spending most of the time in cash. Out-of-sample is the more important signal: Sharpe goes negative (-0.13) and the profit factor drops below 1 (0.56), meaning the strategy's losing trades outweighed its winners in that window, and it lost a small amount of money outright (-0.86%) rather than compounding.

A second caveat that matters for interpreting these numbers correctly: with only 8 trades total (5 in-sample, 3 out-of-sample), the trade-level statistics — win rate, profit factor, average trade return — carry a lot of noise. The entire full-period profit is concentrated almost entirely in a single trade, the COVID-recovery position held from April 2020 to March 2021, which returned 288% and is by far the largest contributor to lifetime P&L; the only other winner returned 10.6%. Remove that one trade and the strategy's full-period numbers look considerably weaker. That fragility is a more important finding than the headline profit factor, and it's the kind of thing worth raising unprompted in an interview rather than waiting to be asked.

*[Insert the equity curve chart, drawdown chart, and trade-marker chart generated in Notebook 3 here before submitting.]*

## Next Steps

The backtest results point to specific priorities, beyond the limitations that were anticipated going in:

- **Signal frequency is too low to be statistically meaningful.** Eight trades over ten years is a small enough sample that win rate and profit factor shouldn't be trusted heavily, and the full-period result hinges on a single trade. Before drawing strong conclusions about whether this approach works, the entry conditions likely need loosening (e.g., a wider RSI band, or relaxing the volume-confirmation requirement) to generate enough trades for the statistics to mean something — done on a different time period or via cross-validation, not by re-tuning against this same backtest's results, which would just be overfitting to the outcome we now know.
- **Time-out-of-market is the main return drag.** The strategy was flat 77% of the time, which explains both its low volatility and its return shortfall versus buy-and-hold. A useful next iteration would track exposure (% of days in position) explicitly as a reported metric, and test whether a less restrictive regime filter recovers more of the upside without giving back the drawdown protection.
- **Long/flat only.** The strategy can't profit from sustained downtrends, and out-of-sample performance (negative Sharpe) suggests the long-only edge may not be reliable on its own. A symmetric short-side rule is worth testing, both for added return potential and as a natural complement to a strategy that's currently only ever long or in cash.
- **No regime detection beyond a moving average.** A 150-day SMA is a blunt instrument, and the strategy's degradation out-of-sample (2022 onward, a choppier period for TSLA than 2015-2021) is consistent with a regime filter that doesn't adapt well to range-bound conditions. A Hidden Markov Model or similar regime classifier is a more direct next step than it looked before seeing these results.
- **Daily bars only.** The task allows for intraday or event-driven trading; this model doesn't use either. Moving to intraday data would require handling market microstructure effects (bid-ask spread, partial fills, more realistic slippage modeling) that a daily-bar backtest can mostly ignore.
- **Walk-forward validation, not just a single train/test split.** The in-sample/out-of-sample split here is a single comparison between two regimes; a proper walk-forward framework re-fitting on rolling windows would give a more robust picture of whether the edge (such as it is) persists across different market conditions, rather than depending on where the split happens to fall.
- **No ensemble or learned overlay.** A gradient-boosted classifier trained on engineered features (RSI, MACD, realized volatility, volume z-scores) could be layered on top of the existing rule-based signal as a confirmation filter, rather than replacing it outright — keeping the interpretable core while picking up incremental signal.
- **No sentiment or order-flow data.** News/social sentiment and large-trade detection were both in scope per the task brief but weren't pursued here, given the time available; they're a natural extension once the core signal is validated.
