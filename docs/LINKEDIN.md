# LinkedIn post (draft)

Post body between the rules (1,2xx characters; limit 1,500).

---

A USD 10 bn stablecoin inflow was associated with 10.9 bp lower 3-month T-bill yields before the GENIUS Act, and 5.6 bp after. No sign that the link got stronger.

The Act (July 2025) caps Treasury reserves at bills and notes maturing within 93 days. Its rules bind from January 2027.

Using open data and pre-registered local projections (Jan 2021 to Oct 2026), I found:

1) Post-enactment, the 3-month response at 10 days is −5.6 bp per USD 10 bn (90% CI −13.0 to +1.9). The change vs. before, +5.3 bp (p = 0.30), has the opposite sign to my hypothesis.
2) The short-end pattern (4-week −14.8 bp vs 2-year ≈ 0) was already there before the Act.
3) Before the Act, outflows were associated with far larger moves than inflows (+16.9 vs −1.6 bp per USD 3.5 bn). That asymmetry is absent after it.

Limits: these are associations, not causal estimates. The post sample is short (~15 months; detectable effect ≈ 15 bp). A placebo break in 2024 is also significant.

Built on Ahmed & Aldasoro (2025), "Stablecoins and safe asset prices", BIS WP 1270. Theirs is the causal design; this is a replication-in-spirit.

Code + data: https://github.com/thanatchon36/stablecoin-tbills-genius-act

#stablecoins #Treasuries #BIS #monetarypolicy

---

**Chart alt-text (output/figures/fig_linkedin.png):**
Line chart of the 3-month T-bill yield response, in basis points, to a USD 10 bn stablecoin inflow over 0–20 business days, before (grey) and after (blue) the GENIUS Act, with 68% and 90% confidence bands.
Both responses are negative at day 10; the post-enactment line is less negative than the pre-enactment one at every horizon, but the difference is not significant at the 5% level at any horizon.
