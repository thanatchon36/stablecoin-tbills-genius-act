# Table 1 — Primary local projection, 3-month T-bill

| Horizon / scaling | Pre-enactment β | Post-enactment β+δ | Difference δ | N_pre | N_post |
|---|---|---|---|---|---|
| h = 0, per USD 10 bn | -0.95 (1.25) [p=0.45] | -0.45 (1.24) [p=0.71] | 0.50 (0.80) [p=0.53] | 1135 | 322 |
| h = 5, per USD 10 bn | -4.28 (2.70) [p=0.11] | -1.98 (3.53) [p=0.57] | 2.29 (3.00) [p=0.45] | 1135 | 317 |
| h = 10, per USD 10 bn | -10.90 (4.16) [p=0.01] | -5.56 (4.54) [p=0.22] | 5.35 (5.21) [p=0.30] | 1135 | 312 |
| h = 20, per USD 10 bn | -23.88 (8.69) [p=0.01] | -4.31 (7.95) [p=0.59] | 19.57 (11.02) [p=0.08] | 1135 | 302 |
| h = 10, per 1 s.d. of F (USD 1.81 bn) | -1.97 (0.75) [p=0.01] | -1.01 (0.82) [p=0.22] | 0.97 (0.94) [p=0.30] | 1135 | 312 |
| h = 10, per USD 3.5 bn (anchor-paper scale) | -3.82 (1.45) [p=0.01] | -1.94 (1.59) [p=0.22] | 1.87 (1.82) [p=0.30] | 1135 | 312 |

Dependent variable: change in the 3-month T-bill yield (DTB3) from t−1 to t+h, bp. F = 5-business-day change in fiat-backed stablecoin supply. Coefficients scaled to the stated flow size; Newey–West SEs (maxlags = h+1) in parentheses; two-sided p-values in brackets. Sample 2021-01-04 to 2026-10-29 (last t for h = 0); break 2025-07-18. Controls: lags 1–5 of Δy and daily flow; ΔDGS2, ΔVIX, BTC and S&P 500 returns, Δlog(RRP+1).
