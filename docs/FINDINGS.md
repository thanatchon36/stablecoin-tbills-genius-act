# FINDINGS — running log

Times are local (UTC+7). Items marked **post hoc** were not in `docs/PAP.md`.

---

## 2026-10-31 18:05 — Phase 0 start

Mode: autonomous. The user said "execute everything in order until the end", which we read as `MODE: autonomous`, so the run does not stop at the checkpoints.

## 2026-10-31 18:12 — Anchor paper fetched and recorded

**Citation (verified on bis.org):** Ahmed, R. and I. Aldasoro (2025), "Stablecoins and safe asset prices", *BIS Working Papers* No 1270, May 2025 (revised June 2026). JEL E42, E43, G12, G23.
- Landing page: https://www.bis.org/publications/working-paper-1270-stablecoins-and-safe-asset-prices
- PDF: https://www.bis.org/publications/working-paper-1270-stablecoins-and-safe-asset-prices.pdf
- The short URL `https://www.bis.org/publ/work1270.pdf` now 301-redirects to the landing page.

**Two versions exist. This matters for quoting.**

### Version 1 (May 2025), as quoted in the brief

Retrieved via the Wayback Machine snapshot of 2025-05-31 of `bis.org/publ/work1270.pdf`.
- **Sample:** daily, 2021–2025 (to about March 2025).
- **Universe:** six USD-backed stablecoins: USDT, USDC, TUSD, BUSD, FDUSD, PYUSD.
- **Flow:** Flow(5d)_t = MC_t − MC_{t−5}, using market capitalisation. Mean 5-day flow USD 0.82 bn, s.d. USD 1.747 bn.
- **Identification:** the flow is instrumented with cumulative "crypto shocks" (as in Aldasoro et al. 2025).
- **Headline:**
  - "a 2-standard deviation inflow into stablecoins lowers 3-month Treasury yields by 2–2.5 basis points within 10 days, with limited to no spillover effects on longer tenors."
  - **Asymmetry:** "stablecoin outflows raise yields by two to three times as much as inflows lower them." In the asymmetric specification, inflows give about 3 bp after 10 days and a USD 3.5 bn outflow gives +6–8 bp, the latter "less precisely estimated … marginal (in)significance at the 95% level".
- The naive univariate LP gives up to −25 bp over 30 days, which the authors treat as endogeneity-biased.
- **Inference:** Newey–West bands at 68% and 95%.
- The brief's recollection (~USD 3.5 bn → −2 to −2.5 bp within 10 days; outflows 2–3×) **matches Version 1**. ✔

### Version 2 (revised June 2026), the current bis.org PDF

- **Sample:** daily, January 2021 – March 2026, T ≈ 1,362 for the flow series.
- **Universe:** seven coins, the V1 six plus RLUSD. Supply comes from CoinMarketCap market capitalisation; chain-level panels for the IV come from DefiLlama and Token Terminal.
- **Flow:** the 5-day change in aggregate market capitalisation (eq. 1), on trading days. Mean USD 0.88 bn, s.d. USD 1.74 bn, min −4.18, max 11.5. USD 3.5 bn ≈ 2 s.d.
- **Specification, eq. (4):**
  y^{3M}_{t+h} − y^{3M}_{t−1} = α_h + φ_h[y_{t−1} − y_{t−5}] + β_h Flow(5d)_t + Σ_{k∈{FFR,6M,1Y}} γ^k_h [y^k_{t+h} − y^k_{t−1}] + θ₁Q^{3M}_t + θ₂1[Q^{3M}_t>0] + θ₃MPS_t + Λ′X_t + e.
  - The controls include the **forward (lead-h) changes** in FFR, 6M and 1Y yields, 3M bill auction size and an auction-day dummy, and high-frequency monetary-policy surprises (3M OIS, 30-minute window).
  - X_t holds 5-day changes in FFR and 1M–10Y yields, log BTC and ETH, MMF AUM and T-bill ETF flows, plus levels and 5-day changes of VIX, log S&P, gold, Brent, log NEER, CESI, TGA, ON RRP and the Treasury MCI.
- **Identification:** a granular IV (Gabaix–Koijen) built from 226 stablecoin-chain pairs. First-stage HAC F = 54. A 1 s.d. move in the IV corresponds to about USD 0.6 bn of 5-day flow.
- **Headline (IV):** "a $3.5 billion (2-standard deviation) inflow lowers 3-month Treasury bill yields by 0.71 basis points on impact, and up to 4 basis points within 10 days". The trough is about 5 bp at 13 days, with 3–4 bp over h = 10–25.
- **Controls-only arm** (closest to our design): "compresses 3-month T-bill yields by less than 1bp within 10 days, with a trough of about 1.5 bps at 20 days; this controls-only estimate is not statistically distinguishable from zero at conventional levels (except briefly at around 20 days)."
- **Term structure:** the 1-month bill responds significantly; 6-month, 2-year and 10-year show no significant response.
- **State dependence:**
  - The effect is larger during TGA rebuilds (about −8 bp) and at high Treasury MCI (about −9 bp).
  - It also scales with log sector size: −3.7 bp at −1 s.d. vs −8.2 bp at +1 s.d.
  - A **post-2024 dummy** gives about 3.3 bp pre-2024 versus a trough near −10 bp after 2024.
- **The asymmetry result no longer appears** in the June 2026 revision; there is no inflow/outflow split.
- The authors explicitly do **not** use GENIUS passage as an event: "its buildup was a gradual and partly anticipated process … producing only modest stablecoin inflows" (fn. 25).
- **Inference:** Newey–West, 68% and 95% bands. The first-stage table uses 1 lag; the LP lag choice is not stated in the text.

### Implications for our design (recorded before estimation)

1. We follow the brief's pre-registered spec, which is a **controls-only LP** with a much smaller control set than V2. The like-for-like comparison is therefore V2's controls-only arm (< 1 bp at h = 10, insignificant), **not** the IV headline. A weak or null pre-period estimate would be consistent with the anchor paper, not a contradiction of it.
2. In the note we quote V1 numbers as "May 2025 version" and V2 numbers as "June 2026 revision", explicitly. The asymmetry claim (H3) comes from V1 only.
3. What we add: V2's post-2024 dummy is a structural-scale proxy, whereas our break is the legal event (18 Jul 2025), with a term-structure test motivated by the 93-day rule. V2's sample ends March 2026; ours runs to October 2026, which roughly doubles the post-enactment window.

## 2026-10-31 18:12 — Legal facts verified (primary source: govinfo PLAW-119publ27)

- **Public Law 119-27**, S. 1582, "Guiding and Establishing National Innovation for U.S. Stablecoins Act" (GENIUS Act). "Approved July 18, 2025." ✔
- **Legislative history** (from the same document): Senate considered and passed it on May 21 and June 2, 9, 11, 12 and 17 2025, with final Senate passage on **2025-06-17** ✔. The House considered and passed it on **2025-07-17** ✔.
- **§4(a)(1)(A)(iii) reserves** include "Treasury bills, notes, or bonds (I) with a remaining maturity of 93 days or less; or (II) issued with a maturity of 93 days or less". Other eligible reserves are coin and currency, deposits, overnight repo and reverse repo, government MMFs and central bank reserves. **The rule is a 93-day cap on Treasury holdings, not a mandate to hold T-bills.**
- **§20 effective date:** "the earlier of (1) the date that is 18 months after the date of enactment of this Act; or (2) the date that is 120 days after the date on which the primary Federal payment stablecoin regulators issue any final regulations implementing this Act." 18 months after enactment is **18 January 2027**.
- **Rulemaking status (secondary sources, 2026-10-31):**
  - Regulators missed the 1-year (18 Jul 2026) rulemaking deadline (The Block, 2026-07-18).
  - The OCC issued the first final rule on 21 Oct 2026 (OCC Bulletin 2026-50), stating that the rule and the Act take effect **18 January 2027**.
  - Since 21 Oct 2026 + 120 days falls after 18 Jan 2027, the 18-month trigger binds. **No reserve requirement was binding at any point in our sample.**

## 2026-10-31 18:12 — Universe fixed (before any yield data)

- DefiLlama list, 427 assets. Named coins resolved by symbol with pegMechanism = fiat-backed:
  - BUSD → "Binance USD", the Paxos-issued coin. "Binance Peg BUSD", a crypto-backed bridged token, is excluded.
  - USDP → "Pax Dollar".
- The ≥ USD 1 bn fiat-backed rule adds USD1 (3.9 bn), USDG (2.9 bn) and USDGO (1.3 bn).
- BUIDL (2.0 bn) is excluded because it is a tokenised MMF share, not a payment stablecoin.
- Crypto-collateralised and synthetic coins (USDS, DAI, USDe, USDf, USDD, FRAX, …) are excluded from the primary aggregate but are included in "all USD-pegged".
- DefiLlama's most recent row is an intraday snapshot dated the fetch day. It is dropped as incomplete.

## 2026-10-31 18:20 — Phase 1: data

**Vintage:** DefiLlama, FRED and Binance were all fetched on 2026-10-31 around 11:14 UTC. Raw files are under `data/raw/` with UTC timestamps in their names.
- **Fallbacks:** none needed. DefiLlama, FRED and Binance all responded on the first try, so the CoinGecko and Treasury.gov fallbacks were not built (simplicity).
- **DefiLlama ids** (resolved by symbol): USDT 1, USDC 2, FDUSD 119, PYUSD 120, TUSD 7, USDP 11, BUSD 4, RLUSD 250, USD1 262, USDG 286, USDGO 347.
- **First DefiLlama snapshot:**
  - USDT 2017-11-29; USDC 2018-09-11; USDP 2018-09-11; TUSD 2019-01-05; BUSD 2020-04-17;
  - FDUSD 2023-05-27; PYUSD 2023-08-08; RLUSD 2024-08-23; USD1 2025-04-28; USDG 2025-07-12; USDGO 2026-02-17.
  - DefiLlama history starts before 2021-01-01, so the full estimation sample from 2021 is covered.
- **Panel:** built on the DTB3 business-day calendar from **2017-11-28 to 2026-10-29** (2,230 days). The estimation sample starts 2021-01-04: **N_pre = 1,135 and N_post = 322** business days.
  - The post sample has more than 200 days, so the PAP power-warning rule is not triggered, although power remains limited (see results).
- **Gaps:**
  - BUSD has 6 missing days, forward-filled.
  - RLUSD has 20 missing days (2024-08-29 to 2024-09-17, pre-launch, supply ≈ 0), so it is excluded from the aggregate on those days.
  - No other coin has gaps.
- **NaN shares** after alignment in the estimation sample are 0.0% for every variable used in estimation. IORB is NaN before 2021-07-29 (9.9%), but it is not used in any regression. DTWEXBGS is 0.07%.
- **Tests:** 8/8 pass, including the external check. USDT and USDC on 2026-03-31 are within ±30% of Ahmed & Aldasoro's reported USD 184 bn and 80 bn (March 2026).
- **Data note:** ON RRP falls to almost zero after mid-2025 (post mean USD 14 bn, minimum USD 0.03 bn). The pre-registered Δlog(RRP + 1) guard is therefore needed.

**Summary statistics, estimation sample (2021-01-04 to 2026-10-29):**

| Variable | Full mean (s.d.) | Pre mean (s.d.) | Post mean (s.d.) |
|---|---|---|---|
| 5-day flow, primary (USD bn) | 0.82 (1.81) | 0.89 (1.77) | 0.59 (1.91) |
| Primary supply (USD bn) | 164.7 (65.2) | 135.5 (39.4) | 267.7 (12.0) |
| 3-month bill (bp) | 330 (191) | 317 (215) | 377 (20) |
| Daily Δ 3-month bill (bp) | 0.27 (3.44) | 0.37 (3.73) | −0.07 (2.07) |
| VIX | 19.2 (5.1) | 19.6 (5.4) | 17.7 (3.1) |
| ON RRP (USD bn) | 850 (850) | 1,087 (820) | 14 (35) |

- The 5-day flow moments are very close to Ahmed & Aldasoro's (mean 0.88, s.d. 1.74), even though they use CoinMarketCap and seven coins.
- **The post-enactment regime is not "more flow".** Average 5-day inflows are smaller (0.59 vs 0.89 bn), the flow s.d. is similar, and the supply level is about twice as large. Primary supply peaked around USD 281 bn and has drifted down to USD 267 bn by end-October 2026.
- Daily bill-yield volatility is about 45% lower post-enactment (s.d. 2.07 vs 3.73 bp).
