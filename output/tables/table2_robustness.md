# Table 2 — Robustness (pre-registered)

| Check (h = 10, per USD 10 bn) | Pre β | Post β+δ | Difference δ | N_pre / N_post |
|---|---|---|---|---|
| Baseline (primary spec) | -10.90 (4.16) [p=0.01] | -5.56 (4.54) [p=0.22] | 5.35 (5.21) [p=0.30] | 1135 / 312 |
| Alternative break 2025-06-17 (Senate) | -10.89 (4.19) [p=0.01] | -4.86 (4.50) [p=0.28] | 6.03 (5.18) [p=0.24] | 1114 / 333 |
| Placebo break 2024-07-18 (data to 2025-06-16) | -13.46 (4.76) [p<0.01] | 9.64 (6.60) [p=0.14] | 23.10 (7.58) [p<0.01] | 886 / 218 |
| Drop ±10 bdays around Terra, FTX, SVB | -10.67 (4.51) [p=0.02] | -5.55 (4.57) [p=0.22] | 5.12 (5.50) [p=0.35] | 1072 / 312 |
| USDT-only flows | -10.67 (4.87) [p=0.03] | -13.45 (7.08) [p=0.06] | -2.79 (7.46) [p=0.71] | 1135 / 312 |
| USDC-only flows | -16.58 (9.55) [p=0.08] | -3.75 (8.52) [p=0.66] | 12.83 (9.98) [p=0.20] | 1135 / 312 |
| All USD-pegged aggregate | -10.74 (2.62) [p<0.01] | -9.23 (4.42) [p=0.04] | 1.51 (4.60) [p=0.74] | 1135 / 312 |
| 1-day timing shift | -11.06 (4.41) [p=0.01] | -5.72 (4.31) [p=0.18] | 5.34 (5.30) [p=0.31] | 1135 / 312 |
| Flow window k = 1 | -11.54 (4.84) [p=0.02] | -4.02 (7.98) [p=0.61] | 7.51 (10.33) [p=0.47] | 1135 / 312 |
| Flow window k = 10 | -12.42 (3.98) [p<0.01] | -8.01 (2.69) [p<0.01] | 4.42 (3.63) [p=0.22] | 1135 / 312 |
| Lags-only controls | -11.01 (4.41) [p=0.01] | -5.65 (4.54) [p=0.21] | 5.35 (5.28) [p=0.31] | 1135 / 312 |

All rows: DTB3, h = 10, coefficients per USD 10 bn of k-day flow, Newey–West SEs (maxlags = 11), two-sided p-values. 'Pre'/'Post' are relative to each row's break date; in the placebo row 'post' is 2024-07-18 to 2025-06-16 and the GENIUS period is not in the sample. USDT-/USDC-only rows use that coin's own flows. k = 1 and k = 10 rows change the flow window (so 'per USD 10 bn' refers to a 1-day or 10-day flow).
