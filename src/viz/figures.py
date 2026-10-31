"""All figures: one style, 300-dpi PNG + SVG, Source/Note footer on every figure."""

from __future__ import annotations

import json
import logging
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.utils import ROOT  # noqa: E402

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


def make_all(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    fig3_data_overview(cfg, panel)
    res_path = ROOT / cfg["paths"]["tables"] / "lp_results.json"
    if res_path.exists():
        from src.viz.figures_lp import make_lp_figures
        make_lp_figures(cfg, json.loads(res_path.read_text()))
