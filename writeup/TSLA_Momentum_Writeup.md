# Momentum Trading Model for Tesla (TSLA)

## Methodology

The model is a long/flat momentum strategy that trades TSLA against its own price and volume history, using absolute (time-series) rather than relative momentum.

Four conditions combine to generate an entry, each targeting a specific failure mode of a naive moving-average system:

1. **Trend regime** — price above its 150-day SMA. Keeps the strategy out of the market during sustained downtrends rather than trying to catch every short-term bounce.
2. **Momentum trigger** — the 20-day EMA crossing above the 50-day EMA, within the bullish regime. Times entries to the point where short-term momentum is reasserting itself inside an established uptrend.
3. **RSI filter (50–75 band)** — confirms momentum is present without being already exhausted. Entries are skipped above RSI 75, where the move is more likely to be a near-term blow-off than a fresh continuation.
4. **Volume confirmation** — the signal day's volume must exceed its 20-day average, filtering out breakouts on unconvincing, low-conviction trading.

Exits trigger on an EMA cross-under, a close back below the trend SMA, or a 2.5×ATR(14) stop-loss, whichever comes first. Position size is volatility-scaled: each trade risks a fixed 1% of current capital, sized by the distance from entry to the stop.

All parameters (EMA lengths, RSI band, trend window, ATR multiplier, risk-per-trade) were chosen a priori, using standard conventions, before looking at any backtest output — not fit to maximise backtest performance.

Execution is modelled with next-day-open fills, $0.005/share commission, 5 bps slippage, and stops checked against the day's low rather than only the close, so an intraday stop breach is not missed.

## Results

Backtest period: **2015-08-06 to 2025-08-29** (2,532 trading days, after the 150-day SMA warm-up window).

| Metric | Strategy | Buy & Hold TSLA |
|---|---|---|
| Total Return | 11.8% | 1,965.7% |
| CAGR | 1.1% | 35.2% |
| Annualised Volatility | 3.4% | 59.1% |
| Sharpe Ratio | 0.34 | 0.80 |
| Sortino Ratio | 0.18 | 1.19 |
| Max Drawdown | −9.3% | −73.6% |

Trade-level: 8 trades, 25% win rate, 3.38 profit factor, 30.7% average trade return, 71.6 days average holding period. Best trade +288.4% (April 2020 – March 2021), worst trade −13.4%.

**In-sample vs. out-of-sample (split at 2022-01-01):**

| Metric | In-Sample (2015–2021) | Out-of-Sample (2022–2025) |
|---|---|---|
| Strategy Sharpe | 0.48 | −0.13 |
| Strategy Max Drawdown | −8.5% | −4.5% |
| Number of trades | 5 | 3 |
| Win rate | 20% | 33.3% |
| Profit factor | 5.65 | 0.56 |
| Buy & Hold Sharpe | 1.13 | 0.25 |
| Buy & Hold Max Drawdown | −60.6% | −71.7% |

The strategy reduced risk substantially: only in a position 22.6% of the time (573 of 2,532 trading days), with volatility (3.4% vs. 59.1%) and max drawdown (−9.3% vs. −73.6%) far below buy-and-hold. That reduction persists out-of-sample — even as the edge weakened post-2022, drawdown (−4.5%) stayed far smaller than TSLA's own (−71.7%).

Return, including risk-adjusted return, is a weaker result. Buy-and-hold's Sharpe exceeds the strategy's both over the full period (0.80 vs. 0.34) and in-sample (1.13 vs. 0.48). Out-of-sample, Sharpe goes negative (−0.13) and the profit factor drops below 1 (0.56): the strategy's losing trades outweighed its winners in that window.

With only 8 trades total, the trade-level statistics carry substantial noise. The full-period profit is concentrated almost entirely in a single trade — the COVID-recovery position held from April 2020 to March 2021, returning 288% — which accounts for the large majority of lifetime P&L; the only other winner returned 10.6%. Removing that trade leaves the strategy's full-period numbers considerably weaker.

## Next Steps

- **Signal frequency is too low to be statistically meaningful.** Eight trades over ten years is a small enough sample that win rate and profit factor should not be trusted heavily, and the full-period result hinges on a single trade.
- **Time-out-of-market is the main return drag.** The strategy was flat 77% of the time, which explains both its low volatility and its return shortfall versus buy-and-hold.
- **Long/flat only.** The strategy cannot profit from sustained downtrends. Out-of-sample performance (negative Sharpe) suggests the long-only edge may not be reliable on its own.
- **No regime detection beyond a moving average.** A 150-day SMA is a blunt instrument, and the strategy's degradation out-of-sample is consistent with a regime filter that does not adapt well to range-bound conditions.
- **Daily bars only.** Moving to intraday data would require handling market microstructure effects (bid-ask spread, partial fills, more realistic slippage) that a daily-bar backtest can mostly ignore.
- **Walk-forward validation, not just a single train/test split.** A rolling walk-forward framework, re-fitting on rolling windows, would give a more robust picture of whether the edge persists across different market conditions.
- **No ensemble or learned overlay.** A gradient-boosted classifier trained on engineered features (RSI, MACD, realised volatility, volume z-scores) could be layered on top of the existing rule-based signal as a confirmation filter.
- **No sentiment or order-flow data.** News/social sentiment and large-trade detection were both in scope but not pursued here; they are a natural extension once the core signal is validated.
