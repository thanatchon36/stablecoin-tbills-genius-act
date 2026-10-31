"""Print-ready figures for paper/ (IEEEtran conference, two columns).

Drawn at final printed size (one column = 3.5 in) in a Times-compatible serif (STIX, bundled with
matplotlib) so figure text matches the body text and is never rescaled by LaTeX. Fonts are embedded
as Type 42; PDFs carry no timestamps, so rebuilds are byte-stable. No in-figure titles: the LaTeX
caption carries the explanation. Pre-enactment is grey and dashed, post-enactment blue and solid, so
the two regimes stay distinguishable in greyscale print.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MultipleLocator

from src.utils import ROOT

log = logging.getLogger(__name__)
logging.getLogger("fontTools").setLevel(logging.WARNING)

COLUMN_IN = 3.5
PRE, PRE_BAND = "#4d4d4d", "#bdbdbd"
POST, POST_BAND = "#2f5f9e", "#a9c4e4"
DARK, MID, LIGHT = "#163d6b", "#4a7fbf", "#a9c4e4"
ACCENT = "#b2182b"
GRID, TEXT = "#dcdcdc", "#333333"
Z68, Z90 = 0.994, 1.645
SHORT = {"Baseline (primary spec)": "Baseline", "Alternative break 2025-06-17 (Senate)": "Break at Senate passage",
         "Placebo break 2024-07-18 (data to 2025-06-16)": "Placebo break, Jul 2024",
         "Drop ±10 bdays around Terra, FTX, SVB": "Drop Terra/FTX/SVB windows",
         "All USD-pegged aggregate": "All USD-pegged coins", "Flow window k = 1": "Flow window k = 1",
         "Flow window k = 10": "Flow window k = 10"}
TENORS = {"DTB4WK": "4-week", "DTB3": "3-month", "DTB6": "6-month", "DGS1": "1-year", "DGS2": "2-year"}

STYLE = {
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.linewidth": 0.5, "axes.edgecolor": TEXT, "axes.labelcolor": TEXT,
    "xtick.color": TEXT, "ytick.color": TEXT, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2, "ytick.major.size": 2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.4, "axes.axisbelow": True,
    "legend.frameon": False, "lines.linewidth": 1.0, "hatch.linewidth": 0.4, "figure.facecolor": "white",
    "savefig.facecolor": "white", "pdf.fonttype": 42, "ps.fonttype": 42, "svg.hashsalt": "genius-act",
}


def _out() -> Path:
    d = ROOT / "paper" / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save(fig: plt.Figure, stem: str) -> None:
    """Timestamp-free PDF for LaTeX and a 300 dpi PNG for the README/web."""
    out = _out()
    fig.savefig(out / f"{stem}.pdf", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out / f"{stem}.png", dpi=300, metadata={"Software": None})
    plt.close(fig)
    log.info("paper figure written: %s", stem)


def panel_label(ax: plt.Axes, s: str) -> None:
    ax.text(-0.02, 1.02, s, transform=ax.transAxes, ha="right", va="bottom", fontweight="bold", fontsize=8)


def _zero(ax: plt.Axes) -> None:
    ax.axhline(0, color=TEXT, lw=0.5, zorder=1)


def _irf(ax: plt.Axes, d: pd.DataFrame, est: str, scale: float, color: str, band: str, ls: str, label: str) -> None:
    m, s = d[est] * scale, d[f"{est}_se"] * abs(scale)
    ax.fill_between(d["h"], m - Z90 * s, m + Z90 * s, color=band, alpha=0.35, lw=0, zorder=2)
    ax.fill_between(d["h"], m - Z68 * s, m + Z68 * s, color=band, alpha=0.6, lw=0, zorder=2)
    ax.plot(d["h"], m, color=color, ls=ls, lw=1.1, label=label, zorder=3)


def _horizon_axis(ax: plt.Axes) -> None:
    ax.set_xlim(0, 20)
    ax.set_xticks(range(0, 21, 5))


def fig_data(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    coins = pd.read_parquet(ROOT / cfg["paths"]["processed"] / "coins_daily.parquet").fillna(0.0)
    start = pd.Timestamp(cfg["sample"]["estimation_start"])
    coins = coins[(coins.index >= start) & (coins.index <= panel.index[-1])]
    other = coins.drop(columns=["USDT", "USDC"]).sum(axis=1)
    p = panel[panel.index >= start]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(COLUMN_IN, 3.3), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.91, bottom=0.08, hspace=0.22)
    a1.stackplot(coins.index, coins["USDT"], coins["USDC"], other, colors=[DARK, MID, LIGHT],
                 labels=["USDT", "USDC", "Other (9 coins)"], lw=0)
    a1.set_ylabel("Supply (USD bn)")
    a1.set_ylim(0, 300)
    a1.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, handlelength=1.2, columnspacing=1.2,
               borderaxespad=0.2)
    a2.plot(p.index, p["DTB3"] / 100, color=DARK, lw=0.9, label="3-month bill")
    a2.plot(p.index, p["DTB4WK"] / 100, color=ACCENT, lw=0.6, ls=(0, (3, 1.5)), label="4-week bill")
    a2.set_ylabel("Yield (%)")
    a2.set_ylim(0, 6)
    a2.legend(loc="center left", handlelength=1.8, borderaxespad=0.2)
    events = {"terra": "Terra", "ftx": "FTX", "svb": "SVB", "signed": "GENIUS Act"}
    for k, lab in events.items():
        d = pd.Timestamp(cfg["events"][k])
        main = k == "signed"
        for ax in (a1, a2):
            ax.axvline(d, color=TEXT if main else "#8c8c8c", lw=0.7 if main else 0.5,
                       ls="-" if main else (0, (2, 2)), zorder=1)
        a1.annotate(lab, (mdates.date2num(d), 0.97), xycoords=a1.get_xaxis_transform(), xytext=(-1.5, 0), textcoords="offset points",
                    rotation=0 if main else 90, ha="right", va="top", fontsize=6, color=TEXT)
    a2.xaxis.set_major_locator(mdates.YearLocator())
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    a1.set_xlim(start, p.index[-1])
    panel_label(a1, "(a)")
    panel_label(a2, "(b)")
    save(fig, "fig_data")


def fig_irf(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    sc = cfg["lp"]["scale_bn"]
    d = pd.DataFrame(res["primary"])
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 2.35))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.88, bottom=0.17)
    _irf(ax, d, "pre", sc, PRE, PRE_BAND, (0, (4, 2)), "Pre-enactment")
    _irf(ax, d, "post", sc, POST, POST_BAND, "-", "Post-enactment")
    _zero(ax)
    _horizon_axis(ax)
    ax.axvline(cfg["lp"]["primary_horizon"], color="#8c8c8c", lw=0.5, ls=":", zorder=1)
    ax.set_xlabel("Business days after the flow, $h$")
    ax.set_ylabel("Change in 3-month yield (bp)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2, handlelength=2.2)
    save(fig, "fig_irf")


def fig_term(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    sc, H = cfg["lp"]["scale_bn"], cfg["lp"]["primary_horizon"]
    d = pd.DataFrame([pd.DataFrame(v).set_index("h").loc[H].rename(k) for k, v in res["term"].items()])
    x = list(range(len(d)))
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 2.15))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.88, bottom=0.12)
    ax.axvspan(-0.5, 1.5, color="#eef3fa", lw=0, zorder=0)
    ax.text(0.5, 0.97, "eligible reserves (≤ 93 days)", transform=ax.get_xaxis_transform(), ha="center",
            va="top", fontsize=6, color=TEXT)
    for est, col, mk, lab, dx in (("pre", PRE, "s", "Pre-enactment", -0.13), ("post", POST, "o", "Post-enactment", 0.13)):
        m, s = d[est] * sc, d[f"{est}_se"] * sc
        ax.errorbar([i + dx for i in x], m, yerr=Z90 * s, fmt=mk, color=col, ms=3.2, mfc=col, capsize=1.8,
                    elinewidth=0.7, capthick=0.7, lw=0, label=lab, zorder=3)
    _zero(ax)
    ax.set_xticks(x, [TENORS[i] for i in d.index])
    ax.set_xlim(-0.5, len(d) - 0.5)
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("$\\beta_{10}$ (bp per USD 10 bn)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    save(fig, "fig_term")


def fig_asym(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    an = cfg["lp"]["anchor_scale_bn"]
    a = pd.DataFrame(res["asymmetry"])
    fig, axes = plt.subplots(2, 2, figsize=(COLUMN_IN, 3.0), sharex=True, sharey="row")
    fig.subplots_adjust(left=0.13, right=0.98, top=0.93, bottom=0.12, hspace=0.38, wspace=0.12)
    spec = [(0, 0, "pos_pre", an, PRE, PRE_BAND, (0, (4, 2)), "(a) Inflow, pre"),
            (0, 1, "pos_post", an, POST, POST_BAND, "-", "(b) Inflow, post"),
            (1, 0, "neg_pre", -an, PRE, PRE_BAND, (0, (4, 2)), "(c) Outflow, pre"),
            (1, 1, "neg_post", -an, POST, POST_BAND, "-", "(d) Outflow, post")]
    for r, c, est, s, col, band, ls, title in spec:
        ax = axes[r, c]
        _irf(ax, a, est, s, col, band, ls, title)
        _zero(ax)
        _horizon_axis(ax)
        ax.set_title(title, loc="left", fontsize=7, pad=3)
    for r in (0, 1):
        axes[r, 0].set_ylabel("Change in yield (bp)")
    for c in (0, 1):
        axes[1, c].set_xlabel("$h$ (business days)")
    save(fig, "fig_asym")


def fig_robust(cfg: dict[str, Any], res: dict[str, Any]) -> None:
    sc = cfg["lp"]["scale_bn"]
    rows = list(res["robustness"].items())[::-1]
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 2.55))
    fig.subplots_adjust(left=0.47, right=0.97, top=0.97, bottom=0.14)
    for i, (name, r) in enumerate(rows):
        placebo = name.startswith("Placebo")
        base = name.startswith("Baseline")
        col = ACCENT if placebo else (DARK if base else POST)
        m, s = r["diff"] * sc, r["diff_se"] * sc
        ax.plot([m - Z90 * s, m + Z90 * s], [i, i], color=col, lw=0.8, solid_capstyle="butt", zorder=3)
        ax.plot(m, i, marker="D" if base else ("s" if placebo else "o"), color=col, ms=3.2, zorder=4)
    labels = [SHORT.get(n, n).replace("k = ", "$k$ = ") for n, _ in rows]
    ax.set_yticks(range(len(rows)), labels)
    ax.tick_params(axis="y", length=0)
    ax.axvline(0, color=TEXT, lw=0.5)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlabel("$\\delta_{10}$: post minus pre (bp per USD 10 bn)")
    ax.xaxis.set_major_locator(MultipleLocator(10))
    save(fig, "fig_robust")


def make_paper_figures(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    res = json.loads((ROOT / cfg["paths"]["tables"] / "lp_results.json").read_text())
    with plt.rc_context(STYLE):
        fig_data(cfg, panel)
        fig_irf(cfg, res)
        fig_term(cfg, res)
        fig_asym(cfg, res)
        fig_robust(cfg, res)
