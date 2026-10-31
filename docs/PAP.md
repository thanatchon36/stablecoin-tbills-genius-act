# Pre-analysis plan

**Project:** Stablecoin flows and T-bill yields after the GENIUS Act
**Written and committed:** 2026-10-31, before any regression was run. The only data inspected beforehand were the DefiLlama coin *list* (needed to fix the coin universe) and the date range of one DefiLlama history endpoint. No yields were downloaded before this file was committed.
**Status rule:** Anything run later that is not in this document is labelled **post hoc** in `docs/FINDINGS.md` and in the note. The primary specification will not change after results are seen.

## 1. Question

Primary: did the response of US Treasury-bill yields to stablecoin flows change after the GENIUS Act was signed into law (Public Law 119-27, 18 July 2025)?

Secondary (only these two):
1. **Maturity shift.** Did the post-enactment response concentrate at the short end (4-week, 3-month) relative to 6-month, 1-year and 2-year? The Act's reserve list admits Treasury bills, notes or bonds with a remaining maturity of 93 days or less (§4(a)(1)(A)(iii)).
2. **Asymmetry.** Is the effect of outflows still larger than that of inflows after enactment?

**Interpretation constraint.** The Act takes effect on the earlier of 18 months after enactment (18 January 2027) or 120 days after the primary federal regulators issue final regulations (§20). As of the data vintage, the reserve requirements are therefore not yet binding. "Post" means a **post-enactment / anticipation regime, not a compliance regime**.

## 2. Hypotheses (signs assume inflows lower yields, so β < 0)

- **H1:** |β₁₀^post| > |β₁₀^pre| for the 3-month bill, i.e. δ₁₀ < 0 in the primary equation.
- **H2:** after enactment, β₁₀ at 4-week and 3-month is more negative than at 6-month, 1-year and 2-year; before enactment the pattern across tenors is flatter.
- **H3:** outflows move yields more than inflows of the same size, in both regimes: |β⁻₁₀| > |β⁺₁₀| pre and post.

A null result on any hypothesis is a legitimate finding and will be reported as the headline if that is what the data say.

## 3. Data and timing

- **Stablecoin supply (DefiLlama, daily).** The primary aggregate S_t is the sum of the circulating supply (`totalCirculating.peggedUSD`, USD bn) of the fiat-backed USD payment stablecoins listed in `config.yaml`: USDT, USDC, FDUSD, PYUSD, TUSD, USDP, BUSD, RLUSD, USD1, USDG and USDGO. Ids are resolved by symbol. The secondary "all USD-pegged" aggregate is DefiLlama's total `peggedUSD` circulating series.
- **Timing.** A DefiLlama snapshot dated d (00:00 UTC) is the value at the end of US calendar day d−1. The supply for business day t is therefore the snapshot dated t+1. The robustness check "1-day timing shift" instead uses the snapshot dated t.
- **Gaps.** Within a coin, gaps of up to 3 days are forward-filled and logged. On dates with longer gaps the coin is NaN, and the aggregate is set to NaN on those dates (logged) rather than summed over fewer coins. The aggregate is the sum over coins that exist on that date; a coin that has not launched yet (or has been fully wound down after its last observation) contributes zero.
- **Business-day calendar.** Dates on which FRED DTB3 is observed.
- **Yields.** FRED DTB4WK, DTB3, DTB6, DGS1, DGS2, all converted to **basis points**.
- **Controls.** VIXCLS, SP500, RRPONTSYD and DGS2 from FRED; the BTCUSDT daily close from Binance. Level series are forward-filled by at most 3 business days onto the calendar before differencing, so that a market holiday's change accrues to the next open day.
- **Estimation sample.** First business day of 2021 (2021-01-04) to the latest date at which every regressor is observed, aligned with Ahmed & Aldasoro (2025), whose sample starts in January 2021. The panel itself is built from the earliest date available, and that date is reported.

## 4. Primary specification

Jordà (2005) local projections, estimated by OLS on business days t, for horizons h = 0, …, 20:

```
y_{t+h} − y_{t−1} = α_h + β_h·F_t + δ_h·(F_t × Post_t) + γ_h·Post_t + Γ_h′·X_t + ε_{t+h}
```

- **y:** DTB3 in bp.
- **F_t = S_t − S_{t−5}:** the 5-business-day change in the primary aggregate, in USD bn. Weekend changes accrue to Monday.
- **Post_t = 1{t ≥ 2025-07-18}.**
- **X_t, baseline:**
  - lags 1–5 of Δy (the outcome's own daily change, bp);
  - lags 1–5 of the daily flow f_t = S_t − S_{t−1} (USD bn);
  - contemporaneous ΔDGS2_t (bp), ΔVIX_t (points), BTC log-return_t (%), S&P 500 log-return_t (%) and Δlog(RRP_t + 1)×100, with RRP in USD bn. The +1 guards against the near-zero balances of 2025–26.
- Control coefficients are common across regimes. Only the flow and the intercept shift with Post.
- **Inference:** Newey–West HAC with maxlags = h + 1 (Bartlett kernel). Report 68% and 90% bands, using the normal critical values 0.994 and 1.645.
- **Reported quantities:** β_h (pre), β_h + δ_h (post, with SE from the joint covariance), δ_h with its p-value, N_pre and N_post (the counts of t with Post = 0 and 1 in each regression).
- **Scaling:** per USD 10 bn of 5-day flow, i.e. 10×β, and per 1 s.d. of F over the estimation sample. One table row rescales to USD 3.5 bn to compare with Ahmed & Aldasoro (2025).
- **Primary horizon:** h = 10. The headline test is δ₁₀ (two-sided p-value; a one-sided reading for H1 is noted where relevant).
- **Control-set robustness:** "lags only", i.e. dropping the contemporaneous controls. Contemporaneous ΔDGS2, VIX, BTC and S&P can themselves respond to flows (bad controls) but also absorb common risk-on/off and policy news, so both versions are reported and the trade-off is discussed.

## 5. Secondary specifications (pre-registered)

1. **Term structure.** The same model for DTB4WK, DTB6, DGS1 and DGS2, each with its own lags of Δy. For the DGS2 outcome, the contemporaneous ΔDGS2 control is omitted, since it is the outcome's own h = 0 change. The deliverable is β₁₀ pre and post by tenor, with 90% CIs.
2. **Asymmetry.** With F⁺ = max(F, 0) and F⁻ = min(F, 0):
   `y_{t+h} − y_{t−1} = α + β⁺F⁺ + β⁻F⁻ + δ⁺F⁺·Post + δ⁻F⁻·Post + γPost + Γ′X + ε`.
   The response to a USD 10 bn inflow is 10β⁺. The response to a USD 10 bn outflow is −10β⁻, so an outflow raises yields if β⁻ < 0. We report β⁺ and β⁻ in each regime and the Wald test of β⁻ = β⁺ in each regime.
3. **Spread outcome.** DTB3 − EFFR in bp, same right-hand side, with lags of Δ(spread).

## 6. Robustness (pre-registered; only these)

The quantities reported for each check are β₁₀ pre, β₁₀ post and δ₁₀ for DTB3, in `table2_robustness`.

1. Alternative break, 2025-06-17 (Senate passage).
2. Placebo break, 2024-07-18, estimated on data before 2025-06-17 only, so that neither the true nor the alternative break is in the sample.
3. Drop t within ±10 business days of Terra (2022-05-09), FTX (2022-11-08) and SVB (2023-03-10).
4. USDT-only flows. F and the lagged daily flows are built from USDT alone.
5. USDC-only flows, built the same way.
6. The all-USD-pegged aggregate.
7. The 1-day timing shift (snapshot dated t used for day t).
8. Flow window k = 1.
9. Flow window k = 10.
10. Lags-only control set (see §4).

## 7. Decision rules fixed in advance

- If the post sample has fewer than 200 business days, everything is still run and the note carries a power warning.
- Null or opposite-signed results are the headline if that is what we find.
- If a phase runs over budget, optional items and robustness checks are cut first, never the primary specification, the tests or the note.
- We do not run an instrumental-variable (granular IV) strategy. This is a controls-only local projection, and the note says so: it replicates the *controls-only* arm of Ahmed & Aldasoro (2025), not their IV estimate.
- There is no correction for multiple testing. With 5 tenors × 21 horizons × 2 regimes, some individually "significant" coefficients are expected by chance. Inference focuses on the pre-registered h = 10 and on the shape of the whole IRF.
