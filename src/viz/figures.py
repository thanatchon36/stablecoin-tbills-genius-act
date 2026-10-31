"""All figures: one style, 300-dpi PNG + SVG, Source/Note footer on every figure."""

from __future__ import annotations

import json
import logging
import textwrap
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from src.utils import ROOT

log = logging.getLogger(__name__)

# Palette: validated categorical slots 1-3 (dataviz reference palette) + neutral greys for "pre".
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
PRE, PRE_BAND = "#6f6e69", "#c9c8c2"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3de"
SURFACE = "#fcfcfb"
SOURCE = "Source: DefiLlama, FRED (St. Louis Fed), Binance; author's calculations."

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False, "lines.linewidth": 1.8,
    "text.color": INK,
})


def _out(cfg: dict[str, Any]):
    d = ROOT / cfg["paths"]["figures"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def footer(fig: plt.Figure, note: str, y: float = 0.01, size: float = 7.0, width: int = 150) -> None:
    """Source/Note footer, bottom-left, wrapped to `width` characters."""
    body = textwrap.fill(f"Note: {note}", width)
    fig.text(0.01, y, f"{SOURCE}\n{body}", ha="left", va="bottom", fontsize=size, color=INK2)


def save(fig: plt.Figure, cfg: dict[str, Any], name: str, dpi: int = 300) -> None:
    out = _out(cfg)
    fig.savefig(out / f"{name}.png", dpi=dpi)
    fig.savefig(out / f"{name}.svg")
    plt.close(fig)
    log.info("figure written: %s", name)


def fig3_data_overview(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    """Top: stacked primary-universe supply by coin (USDT, USDC, Other). Bottom: 4-week and 3-month bills."""
    coins = pd.read_parquet(ROOT / cfg["paths"]["processed"] / "coins_daily.parquet").fillna(0.0)
    start = pd.Timestamp(cfg["sample"]["estimation_start"])
    coins = coins[(coins.index >= start) & (coins.index <= panel.index[-1])]
    other = coins.drop(columns=["USDT", "USDC"]).sum(axis=1)
    p = panel[panel.index >= start]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 6.4), sharex=True, gridspec_kw={"height_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.17, hspace=0.18)
    a1.stackplot(coins.index, coins["USDT"], coins["USDC"], other, colors=[BLUE, ORANGE, AQUA],
                 labels=["USDT", "USDC", "Other fiat-backed (9 coins)"], edgecolor=SURFACE, linewidth=0.3)
    a1.set_ylabel("Circulating supply (USD bn)")
    a1.legend(loc="upper left", ncol=3, fontsize=8)
    a1.set_title("Fiat-backed USD stablecoin supply", loc="left")
    a2.plot(p.index, p["DTB4WK"] / 100, color=BLUE, lw=1.4, label="4-week bill")
    a2.plot(p.index, p["DTB3"] / 100, color=ORANGE, lw=1.4, label="3-month bill")
    a2.set_ylabel("Yield (%)")
    a2.legend(loc="center left", ncol=1, fontsize=8)
    a2.set_title("US Treasury bill yields (secondary market, discount basis)", loc="left")
    labels = {"terra": "Terra", "ftx": "FTX", "svb": "SVB", "tariffs": "Tariffs", "senate_passes": "Senate",
              "signed": "GENIUS signed"}
    for k, lab in labels.items():
        d = pd.Timestamp(cfg["events"][k])
        for ax in (a1, a2):
            ax.axvline(d, color=INK if k == "signed" else INK2, lw=1.0 if k == "signed" else 0.7,
                       ls="-" if k == "signed" else (0, (3, 3)), zorder=0)
        dx = -2 if k == "senate_passes" else 2
        a2.annotate(lab, (d, 5.95), xytext=(dx, 0), textcoords="offset points", rotation=90, va="top",
                    ha="right" if dx < 0 else "left", fontsize=7, color=INK2)
    a2.set_ylim(0, 6)
    a2.xaxis.set_major_locator(mdates.YearLocator())
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.suptitle("Stablecoin supply and short-term Treasury yields, 2021–2026", x=0.01, ha="left", fontsize=12,
                 fontweight="bold")
    footer(fig, f"Daily, {start.date()} to {panel.index[-1].date()}. Supply is DefiLlama circulating supply; each 00:00 "
                "UTC snapshot is assigned to the end of the previous US day. 'Other' = FDUSD, PYUSD, TUSD, USDP, BUSD, RLUSD, USD1, USDG, USDGO. "
                "Vertical lines: Terra (9 May 2022), FTX (8 Nov 2022), SVB (10 Mar 2023), tariffs (2 Apr 2025), "
                "Senate passage (17 Jun 2025), signing (18 Jul 2025, solid).")
    save(fig, cfg, "fig3_data_overview")


Z68, Z90 = 0.994, 1.645
TENORS = {"DTB4WK": "4-week", "DTB3": "3-month", "DTB6": "6-month", "DGS1": "1-year", "DGS2": "2-year"}


def _irf(ax: plt.Axes, df: pd.DataFrame, est: str, se: str, scale: float, color: str, band: str,
         label: str, dodge: float = 0.0) -> None:
    """IRF line with 90% (light) and 68% (darker) bands; abs(scale) for SEs."""
    h = df["h"] + dodge
    m, s = df[est] * scale, df[se] * abs(scale)
    ax.fill_between(h, m - Z90 * s, m + Z90 * s, color=band, alpha=0.35, lw=0)
    ax.fill_between(h, m - Z68 * s, m + Z68 * s, color=band, alpha=0.55, lw=0)
    ax.plot(h, m, color=color, lw=2.0, label=label, marker="o", ms=2.5)


def _zero(ax: plt.Axes) -> None:
    ax.axhline(0, color=INK2, lw=0.8)


def fig1_irf_pre_post(cfg: dict[str, Any], res: dict[str, Any], linkedin: bool = False) -> None:
    """Hero figure: DTB3 IRF pre vs post, per USD 10 bn of 5-day inflow."""
    sc = cfg["lp"]["scale_bn"]
    d = pd.DataFrame(res["primary"])
    r10 = d.set_index("h").loc[10]
    if linkedin:
        fig, ax = plt.subplots(figsize=(6, 6))
        fig.subplots_adjust(left=0.13, right=0.96, top=0.78, bottom=0.2)
    else:
        fig, ax = plt.subplots(figsize=(8, 5.2))
        fig.subplots_adjust(left=0.09, right=0.97, top=0.83, bottom=0.2)
    _irf(ax, d, "pre", "pre_se", sc, PRE, PRE_BAND, "Pre-enactment (2021-01 to 2025-07-17)")
    _irf(ax, d, "post", "post_se", sc, BLUE, "#86b6ef", "Post-enactment (2025-07-18 to 2026-10)")
    _zero(ax)
    ax.set_xlim(0, 20)
    ax.set_xticks(range(0, 21, 5))
    ax.set_xlabel("Business days after the flow (h)")
    ax.set_ylabel("Change in 3-month T-bill yield (bp)")
    last = d.iloc[-1]
    ax.annotate("pre", (20, last.pre * sc), xytext=(-4, -12), textcoords="offset points", ha="right", color=INK2)
    ax.annotate("post", (20, last.post * sc), xytext=(-4, 8), textcoords="offset points", ha="right", color=INK2)
    ax.legend(loc="lower left", fontsize=8 if not linkedin else 9)
    sub = (f"Per USD 10 bn 5-day inflow into fiat-backed stablecoins. N_pre = {int(r10.N_pre)}, "
           f"N_post = {int(r10.N_post)} business days (h = 10). At h = 10: pre {r10.pre*sc:.1f} bp, "
           f"post {r10.post*sc:.1f} bp, difference p = {r10.diff_p:.2f}.")
    if linkedin:
        fig.suptitle("Since the GENIUS Act, stablecoin inflows have not\nmoved 3-month T-bill yields more than before",
                     x=0.02, y=0.975, ha="left", fontsize=14, fontweight="bold")
        fig.text(0.02, 0.83, textwrap.fill(sub, 85), fontsize=9, color=INK2)
        ax.tick_params(labelsize=10)
        ax.xaxis.label.set_size(11)
        ax.yaxis.label.set_size(11)
        footer(fig, "Local projections with controls (not IV); 68% and 90% Newey–West bands. Association, not "
                    "causation. Code + data: github.com/<my-handle>/stablecoin-tbills-genius-act", size=8, width=95)
        save(fig, cfg, "fig_linkedin", dpi=200)
    else:
        fig.suptitle("3-month T-bill response to stablecoin inflows, before vs after the GENIUS Act",
                     x=0.01, ha="left", fontsize=12, fontweight="bold")
        fig.text(0.01, 0.885, textwrap.fill(sub, 125), fontsize=8.5, color=INK2)
        footer(fig, "Jordà local projection of y(t+h) − y(t−1) on the 5-day flow, flow × Post, Post and controls "
                    "(lags 1–5 of Δy and daily flow; ΔDGS2, ΔVIX, BTC and S&P 500 returns, Δlog RRP). Lines: point "
                    "estimates; shaded: 68% (dark) and 90% (light) Newey–West bands (maxlags = h+1). Post = signed "
                    "into law 18 Jul 2025; reserve rules not yet binding (effective 18 Jan 2027). Controls-only, "
                    "not instrumented: association, not causation.")
        save(fig, cfg, "fig1_irf_pre_post")


def fig2_term_structure(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    sc = cfg["lp"]["scale_bn"]
    rows = [pd.DataFrame(v).set_index("h").loc[10].rename(k) for k, v in res["term"].items()]
    d = pd.DataFrame(rows)
    x = range(len(d))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.85, bottom=0.22)
    for est, se, col, lab, dx in [("pre", "pre_se", PRE, "Pre-enactment", -0.12),
                                  ("post", "post_se", BLUE, "Post-enactment", 0.12)]:
        m, s = d[est] * sc, d[se] * sc
        ax.errorbar([i + dx for i in x], m, yerr=Z90 * s, fmt="o", color=col, ms=6, capsize=3, lw=1.6, label=lab)
    _zero(ax)
    ax.axvspan(-0.5, 1.5, color="#eef4fc", zorder=0, lw=0)
    ax.text(0.5, ax.get_ylim()[1], "≤ 93 days (GENIUS-eligible)", ha="center", va="top", fontsize=8, color=INK2)
    ax.set_xticks(list(x), [TENORS[i] for i in d.index])
    ax.set_xlim(-0.5, len(d) - 0.5)
    ax.set_ylabel("β₁₀: bp per USD 10 bn 5-day inflow")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.suptitle("Response after 10 business days, by tenor", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, 0.895, "Point estimates with 90% Newey–West confidence intervals, pre vs post enactment.",
             fontsize=8.5, color=INK2)
    footer(fig, "Same local projection as Figure 1 with the outcome replaced by each tenor (4-week, 3-month and "
                "6-month bills: secondary-market discount yields; 1-year and 2-year: constant-maturity yields). "
                "ΔDGS2 control omitted for the 2-year outcome. Shaded band: maturities eligible as reserves under "
                "§4(a)(1)(A)(iii) of the GENIUS Act.")
    save(fig, cfg, "fig2_term_structure")


def fig4_asymmetry(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    sc = cfg["lp"]["anchor_scale_bn"]
    a = pd.DataFrame(res["asymmetry"])
    od = res["outflow_days"]
    fig, axes = plt.subplots(2, 2, figsize=(8, 6.2), sharex=True)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.86, bottom=0.2, hspace=0.32, wspace=0.18)
    panels = [(0, 0, "pos_pre", sc, PRE, PRE_BAND, "Inflow, pre-enactment"),
              (0, 1, "pos_post", sc, BLUE, "#86b6ef", "Inflow, post-enactment"),
              (1, 0, "neg_pre", -sc, PRE, PRE_BAND, "Outflow, pre-enactment"),
              (1, 1, "neg_post", -sc, BLUE, "#86b6ef", "Outflow, post-enactment")]
    for r, c, est, s, col, band, title in panels:
        ax = axes[r, c]
        _irf(ax, a, est, est + "_se", s, col, band, title)
        _zero(ax)
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.set_xlim(0, 20)
        ax.set_xticks(range(0, 21, 5))
    for r in (0, 1):
        lo = min(axes[r, 0].get_ylim()[0], axes[r, 1].get_ylim()[0])
        hi = max(axes[r, 0].get_ylim()[1], axes[r, 1].get_ylim()[1])
        for c in (0, 1):
            axes[r, c].set_ylim(lo, hi)
    axes[0, 0].set_ylabel("Δ 3-month yield (bp)")
    axes[1, 0].set_ylabel("Δ 3-month yield (bp)")
    for c in (0, 1):
        axes[1, c].set_xlabel("Business days after the flow (h)")
    fig.suptitle("Inflows vs outflows: response to a USD 3.5 bn 5-day flow", x=0.01, ha="left", fontsize=12,
                 fontweight="bold")
    fig.text(0.01, 0.895, textwrap.fill("Top row: yield change after a USD 3.5 bn inflow. Bottom row: after a USD "
                                        "3.5 bn outflow (positive = outflows raise yields). Rows have different "
                                        "y-scales.", 125), fontsize=8.5, color=INK2)
    footer(fig, "Local projection with F⁺ = max(F,0) and F⁻ = min(F,0), each interacted with Post; other terms as in "
                "Figure 1. USD 3.5 bn (≈2 s.d.) follows Ahmed & Aldasoro (2025). 68% and 90% Newey–West bands. "
                f"Pre-enactment outflow days are concentrated in 2022–23 ({od['pre_2022_2023']} of {od['pre']}), during the "
                "Fed hiking cycle.")
    save(fig, cfg, "fig4_asymmetry")


def make_all(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    fig3_data_overview(cfg, panel)
    res = json.loads((ROOT / cfg["paths"]["tables"] / "lp_results.json").read_text())
    fig1_irf_pre_post(cfg, res)
    fig1_irf_pre_post(cfg, res, linkedin=True)
    fig2_term_structure(cfg, res)
    fig4_asymmetry(cfg, res)
