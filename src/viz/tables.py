"""Tables from output/tables/lp_results.json (.md for the note, .csv for machines).

All coefficients are rescaled from "bp per USD 1 bn" to "bp per USD 10 bn" unless stated otherwise.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd

from src.utils import ROOT

log = logging.getLogger(__name__)


def md_table(df: pd.DataFrame) -> str:
    """Minimal GitHub-markdown table (no extra dependency)."""
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines) + "\n"


def cell(est: float, se: float, scale: float, p: float | None = None) -> str:
    s = f"{est * scale:.2f} ({se * abs(scale):.2f})"
    if p is None:
        return s
    return s + (" [p<0.01]" if p < 0.005 else f" [p={p:.2f}]")


def table1(res: dict[str, Any], cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    lp = cfg["lp"]
    prim = pd.DataFrame(res["primary"]).set_index("h")
    sd = res["flow_sd_bn"]
    rows, csv = [], []
    scalings = [(h, lp["scale_bn"], f"h = {h}, per USD 10 bn") for h in (0, 5, 10, 20)]
    scalings += [(lp["primary_horizon"], sd, f"h = 10, per 1 s.d. of F (USD {sd:.2f} bn)"),
                 (lp["primary_horizon"], lp["anchor_scale_bn"], "h = 10, per USD 3.5 bn (anchor-paper scale)")]
    for h, sc, label in scalings:
        r = prim.loc[h]
        rows.append({"Horizon / scaling": label,
                     "Pre-enactment β": cell(r.pre, r.pre_se, sc, r.pre_p),
                     "Post-enactment β+δ": cell(r.post, r.post_se, sc, r.post_p),
                     "Difference δ": cell(r["diff"], r.diff_se, sc, r.diff_p),
                     "N_pre": int(r.N_pre), "N_post": int(r.N_post)})
        csv.append({"h": h, "scale_bn": sc, **{k: r[k] * sc for k in ("pre", "pre_se", "post", "post_se", "diff", "diff_se")},
                    **{k: r[k] for k in ("pre_p", "post_p", "diff_p", "N_pre", "N_post", "start", "end")}})
    df = pd.DataFrame(rows)
    note = (f"\nDependent variable: change in the 3-month T-bill yield (DTB3) from t−1 to t+h, bp. "
            f"F = 5-business-day change in fiat-backed stablecoin supply. Coefficients scaled to the stated flow size; "
            f"Newey–West SEs (maxlags = h+1) in parentheses; two-sided p-values in brackets. Sample "
            f"{prim.loc[0, 'start']} to {prim.loc[0, 'end']} (last t for h = 0); break 2025-07-18. "
            "Controls: lags 1–5 of Δy and daily flow; ΔDGS2, ΔVIX, BTC and S&P 500 returns, Δlog(RRP+1).\n")
    return pd.DataFrame(csv), "# Table 1 — Primary local projection, 3-month T-bill\n\n" + md_table(df) + note


def table2(res: dict[str, Any], cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    sc = cfg["lp"]["scale_bn"]
    rows, csv = [], []
    for name, r in res["robustness"].items():
        rows.append({"Check (h = 10, per USD 10 bn)": name, "Pre β": cell(r["pre"], r["pre_se"], sc, r["pre_p"]),
                     "Post β+δ": cell(r["post"], r["post_se"], sc, r["post_p"]),
                     "Difference δ": cell(r["diff"], r["diff_se"], sc, r["diff_p"]),
                     "N_pre / N_post": f"{r['N_pre']} / {r['N_post']}"})
        csv.append({"check": name, **{k: r[k] * sc for k in ("pre", "pre_se", "post", "post_se", "diff", "diff_se")},
                    **{k: r[k] for k in ("pre_p", "post_p", "diff_p", "N_pre", "N_post", "flow_sd_bn")}})
    note = ("\nAll rows: DTB3, h = 10, coefficients per USD 10 bn of k-day flow, Newey–West SEs (maxlags = 11), "
            "two-sided p-values. 'Pre'/'Post' are relative to each row's break date; in the placebo row 'post' "
            "is 2024-07-18 to 2025-06-16 and the GENIUS period is not in the sample. USDT-/USDC-only rows use that "
            "coin's own flows. k = 1 and k = 10 rows change the flow window (so 'per USD 10 bn' refers to a 1-day or "
            "10-day flow).\n")
    return pd.DataFrame(csv), "# Table 2 — Robustness (pre-registered)\n\n" + md_table(pd.DataFrame(rows)) + note


def table3_term(res: dict[str, Any], cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    sc = cfg["lp"]["scale_bn"]
    names = {"DTB4WK": "4-week bill", "DTB3": "3-month bill", "DTB6": "6-month bill", "DGS1": "1-year CMT",
             "DGS2": "2-year CMT"}
    rows, csv = [], []
    for y, recs in res["term"].items():
        r = pd.DataFrame(recs).set_index("h").loc[cfg["lp"]["primary_horizon"]]
        rows.append({"Tenor": names[y], "Pre β₁₀": cell(r.pre, r.pre_se, sc, r.pre_p),
                     "Post β₁₀": cell(r.post, r.post_se, sc, r.post_p),
                     "Difference δ₁₀": cell(r["diff"], r.diff_se, sc, r.diff_p)})
        csv.append({"outcome": y, **{k: r[k] * sc for k in ("pre", "pre_se", "post", "post_se", "diff", "diff_se")},
                    **{k: r[k] for k in ("pre_p", "post_p", "diff_p", "N_pre", "N_post")}})
    note = "\nh = 10, bp per USD 10 bn of 5-day flow, Newey–West SEs; same controls as Table 1 (ΔDGS2 omitted for the 2-year outcome).\n"
    return pd.DataFrame(csv), "# Table 3 — Term structure of β₁₀ (secondary, pre-registered)\n\n" + md_table(pd.DataFrame(rows)) + note


def table4_asym(res: dict[str, Any], cfg: dict[str, Any]) -> tuple[pd.DataFrame, str]:
    """Responses to a USD 3.5 bn inflow (= 3.5·β⁺) and a USD 3.5 bn outflow (= −3.5·β⁻)."""
    sc = cfg["lp"]["anchor_scale_bn"]
    a = pd.DataFrame(res["asymmetry"]).set_index("h")
    rows, csv = [], []
    for h in (0, 5, 10, 20):
        r = a.loc[h]
        rows.append({"h": h,
                     "Pre: inflow": cell(r.pos_pre, r.pos_pre_se, sc, r.pos_pre_p),
                     "Pre: outflow": cell(r.neg_pre, r.neg_pre_se, -sc, r.neg_pre_p),
                     "Pre: p(β⁻=β⁺)": f"{r.asym_pre_p:.2f}",
                     "Post: inflow": cell(r.pos_post, r.pos_post_se, sc, r.pos_post_p),
                     "Post: outflow": cell(r.neg_post, r.neg_post_se, -sc, r.neg_post_p),
                     "Post: p(β⁻=β⁺)": f"{r.asym_post_p:.2f}"})
        csv.append({"h": h, "inflow_pre": r.pos_pre * sc, "inflow_pre_se": r.pos_pre_se * sc,
                    "outflow_pre": -r.neg_pre * sc, "outflow_pre_se": r.neg_pre_se * sc,
                    "inflow_post": r.pos_post * sc, "inflow_post_se": r.pos_post_se * sc,
                    "outflow_post": -r.neg_post * sc, "outflow_post_se": r.neg_post_se * sc,
                    "asym_pre_p": r.asym_pre_p, "asym_post_p": r.asym_post_p})
    note = ("\nYield response (bp) to a USD 3.5 bn 5-day inflow (3.5·β⁺) and to a USD 3.5 bn 5-day outflow (−3.5·β⁻); "
            "a positive outflow entry means outflows raise yields. Newey–West SEs in parentheses. p(β⁻=β⁺): Wald test "
            "of equal slopes within the regime.\n")
    return pd.DataFrame(csv), "# Table 4 — Asymmetry (secondary, pre-registered)\n\n" + md_table(pd.DataFrame(rows)) + note


def make_tables(cfg: dict[str, Any]) -> None:
    out = ROOT / cfg["paths"]["tables"]
    res = json.loads((out / "lp_results.json").read_text())
    for name, fn in [("table1_primary", table1), ("table2_robustness", table2), ("table3_term_structure", table3_term),
                     ("table4_asymmetry", table4_asym)]:
        csv, md = fn(res, cfg)
        csv.to_csv(out / f"{name}.csv", index=False)
        (out / f"{name}.md").write_text(md)
        log.info("table written: %s", name)
