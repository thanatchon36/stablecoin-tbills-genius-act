"""Generate paper/numbers.tex (one LaTeX macro per result quoted in the paper) and paper/tables/*.tex.

Every macro and table cell is read from output/tables/lp_results.json, output/tables/summary_stats.csv,
data/processed/meta.json or the panel, so the paper's prose never carries a hand-typed result.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import ROOT

log = logging.getLogger(__name__)

PAPER = ROOT / "paper"
TENOR_KEYS = {"DTB4WK": "FourW", "DTB3": "ThreeM", "DTB6": "SixM", "DGS1": "OneY", "DGS2": "TwoY"}
TENOR_NAMES = {"DTB4WK": "4-week bill", "DTB3": "3-month bill", "DTB6": "6-month bill", "DGS1": "1-year CMT",
               "DGS2": "2-year CMT"}
Z90 = 1.645


def num(x: float, d: int = 1, plus: bool = False) -> str:
    """Number with a typographic minus (and optional explicit plus)."""
    s = f"{x:.{d}f}"
    if s.startswith("-") and float(s) != 0:
        return "\\ensuremath{-}" + s[1:]
    s = s.lstrip("-")
    return "+" + s if plus else s


def pval(p: float) -> str:
    """p-value for table cells."""
    return "$<$0.01" if p < 0.005 else f"{p:.2f}"


def ptext(p: float) -> str:
    """p-value for prose, with its own relation: '$p=0.30$' or '$p<0.01$'."""
    return "$p<0.01$" if p < 0.005 else f"$p={p:.2f}$"


def tex_date(d: str | pd.Timestamp) -> str:
    t = pd.Timestamp(d)
    return f"{t.day}~{t:%B %Y}"


def _h(recs: list[dict[str, Any]], h: int) -> pd.Series:
    return pd.DataFrame(recs).set_index("h").loc[h]


def numbers(cfg: dict[str, Any], res: dict[str, Any], stats: pd.DataFrame, meta: dict[str, Any],
            panel: pd.DataFrame) -> dict[str, str]:
    lp = cfg["lp"]
    sc, an, H = lp["scale_bn"], lp["anchor_scale_bn"], lp["primary_horizon"]
    sd = res["flow_sd_bn"]
    m: dict[str, str] = {}

    # Sample and data
    p10 = _h(res["primary"], H)
    p0 = _h(res["primary"], 0)
    m["nPre"], m["nPost"], m["nPostTen"] = f"{int(p0.N_pre):,}", str(int(p0.N_post)), str(int(p10.N_post))
    m["sampleStart"], m["sampleEnd"] = tex_date(p0.start), tex_date(p0.end)
    m["vintage"] = tex_date(meta["vintage_fred_utc"][:10])
    m["nCoins"] = str(len(meta["defillama_ids"]))
    st = stats.set_index(["regime", "variable"])
    flow = "5-day flow, primary (USD bn)"
    for reg, tag in (("full", ""), ("pre", "Pre"), ("post", "Post")):
        m[f"flowMean{tag}"] = num(st.loc[(reg, flow), "mean"], 2)
        m[f"flowSD{tag}"] = num(st.loc[(reg, flow), "sd"], 2)
        m[f"dyThreeSD{tag}"] = num(st.loc[(reg, "Daily change 3-month bill (bp)"), "sd"], 2)
        m[f"supplyMean{tag}"] = num(st.loc[(reg, "Primary supply (USD bn)"), "mean"], 0)
    m["supplyEnd"] = num(panel["S_primary"].dropna().iloc[-1], 0)
    m["supplyPeak"] = num(panel["S_primary"].max(), 0)
    m["rrpPostMean"] = num(st.loc[("post", "ON RRP (USD bn)"), "mean"], 0)
    m["rrpPreMean"] = num(st.loc[("pre", "ON RRP (USD bn)"), "mean"], 0)
    od = res["outflow_days"]
    m["outPre"], m["outPost"], m["outPreHike"] = str(od["pre"]), str(od["post"]), str(od["pre_2022_2023"])
    m["flowSDbn"] = num(sd, 2)

    # Primary LP (per USD 10 bn unless stated)
    def put(prefix: str, r: pd.Series, scale: float) -> None:
        for k, tag in (("pre", "Pre"), ("post", "Post"), ("diff", "Diff")):
            m[f"{prefix}{tag}"] = num(r[k] * scale, 1, plus=(k == "diff"))
            m[f"{prefix}{tag}SE"] = num(r[f"{k}_se"] * abs(scale), 1)
            m[f"{prefix}{tag}P"] = ptext(r[f"{k}_p"])
            m[f"{prefix}{tag}Lo"] = num((r[k] - Z90 * r[f"{k}_se"]) * scale, 1)
            m[f"{prefix}{tag}Hi"] = num((r[k] + Z90 * r[f"{k}_se"]) * scale, 1, plus=True)

    put("b", p10, sc)
    put("bTw", _h(res["primary"], 20), sc)
    put("bFive", _h(res["primary"], 5), sc)
    put("bAnchor", p10, an)
    put("bSD", p10, sd)
    put("bLags", _h(res["primary_lags_only"], H), sc)
    prim = pd.DataFrame(res["primary"]).set_index("h")
    trough = (prim["post"] * sc).idxmin()
    m["postTrough"], m["postTroughH"] = num(prim.loc[trough, "post"] * sc, 1), str(int(trough))
    m["mde"] = f"{2.80 * p10.diff_se * sc:.0f}"
    m["mdeRatio"] = num(2.80 * p10.diff_se / abs(p10.pre), 1)

    # Term structure
    diffp = []
    for y, recs in res["term"].items():
        r = _h(recs, H)
        put(f"t{TENOR_KEYS[y]}", r, sc)
        diffp.append(r.diff_p)
    m["termDiffMinP"] = f"{min(diffp):.2f}"

    # Asymmetry (per USD 3.5 bn; outflow response = -3.5 * beta_neg)
    for h, tag in ((H, ""), (20, "Tw")):
        a = _h(res["asymmetry"], h)
        for reg, R in (("pre", "Pre"), ("post", "Post")):
            m[f"aIn{R}{tag}"] = num(a[f"pos_{reg}"] * an, 1, plus=True)
            m[f"aIn{R}{tag}P"] = ptext(a[f"pos_{reg}_p"])
            m[f"aOut{R}{tag}"] = num(-a[f"neg_{reg}"] * an, 1, plus=True)
            m[f"aOut{R}{tag}P"] = ptext(a[f"neg_{reg}_p"])
            m[f"aEq{R}{tag}P"] = ptext(a[f"asym_{reg}_p"])

    # Spread
    put("sp", _h(res["spread"], H), sc)

    # Robustness
    rb = res["robustness"]
    nonpl = {k: v for k, v in rb.items() if not k.startswith("Placebo")}
    m["rbN"] = str(len(nonpl))
    m["rbNPos"] = str(sum(v["diff"] > 0 for v in nonpl.values()))
    m["rbMinP"] = ptext(min(v["diff_p"] for v in nonpl.values()))
    for key, name in (("rbUSDT", "USDT-only flows"), ("rbUSDC", "USDC-only flows"), ("rbAll", "All USD-pegged aggregate"),
                      ("rbKten", "Flow window k = 10"), ("rbKone", "Flow window k = 1"),
                      ("rbAlt", "Alternative break 2025-06-17 (Senate)"),
                      ("rbPl", "Placebo break 2024-07-18 (data to 2025-06-16)"),
                      ("rbTiming", "1-day timing shift"), ("rbDrop", "Drop ±10 bdays around Terra, FTX, SVB")):
        put(key, pd.Series(rb[name]), sc)
    return m


def write_numbers(m: dict[str, str], path: Path) -> None:
    header = ("% Generated by src/viz/paper_tex.py from output/tables/lp_results.json, summary_stats.csv and "
              "data/processed/meta.json. Do not edit.")
    lines = [header]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(m.items())]
    path.write_text("\n".join(lines) + "\n")


def _cell(r: pd.Series | dict[str, Any], k: str, scale: float, plus: bool = False) -> str:
    return f"{num(r[k] * scale, 2, plus)} ({num(r[f'{k}_se'] * abs(scale), 2)})"


def tab_primary(cfg: dict[str, Any], res: dict[str, Any]) -> str:
    lp = cfg["lp"]
    sd = res["flow_sd_bn"]
    rows = [(h, lp["scale_bn"], f"$h={h}$, per USD 10\\,bn") for h in (0, 5, 10, 20)]
    rows += [(10, sd, f"$h=10$, per 1 s.d. (USD {sd:.2f}\\,bn)"), (10, lp["anchor_scale_bn"], "$h=10$, per USD 3.5\\,bn")]
    body = []
    for h, s, lab in rows:
        r = _h(res["primary"], h)
        body.append(f"{lab} & {_cell(r, 'pre', s)} & {pval(r.pre_p)} & {_cell(r, 'post', s)} & {pval(r.post_p)} & "
                    f"{_cell(r, 'diff', s, True)} & {pval(r.diff_p)} & {int(r.N_pre)} & {int(r.N_post)} \\\\")
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrrrrrrrr}\n\\toprule\n"
            " & \\multicolumn{2}{c}{Pre-enactment $\\beta_h$} & \\multicolumn{2}{c}{Post-enactment $\\beta_h+\\delta_h$}"
            " & \\multicolumn{2}{c}{Difference $\\delta_h$} & & \\\\\n"
            "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n"
            "Horizon, scaling & est. (s.e.) & $p$ & est. (s.e.) & $p$ & est. (s.e.) & $p$ & $N_{pre}$ & $N_{post}$ \\\\\n"
            "\\midrule\n" + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}\n")


def tab_robust(cfg: dict[str, Any], res: dict[str, Any]) -> str:
    sc = cfg["lp"]["scale_bn"]
    body = []
    for name, r in res["robustness"].items():
        lab = re.sub(r"k = (\\d+)", r"$k=\\1$", name.replace("±", "$\\pm$").replace("bdays", "business days"))
        if name.startswith("Placebo"):
            body.append("\\midrule")
        body.append(f"{lab} & {_cell(r, 'pre', sc)} & {_cell(r, 'post', sc)} & {_cell(r, 'diff', sc, True)} & "
                    f"{pval(r['diff_p'])} & {r['N_pre']}\\,/\\,{r['N_post']} \\\\")
        if name.startswith("Placebo"):
            body.append("\\midrule")
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrrrrr}\n\\toprule\n"
            "Specification ($h=10$, per USD 10\\,bn) & Pre $\\beta$ & Post $\\beta+\\delta$ & $\\delta$ & $p(\\delta)$ & "
            "$N_{pre}$\\,/\\,$N_{post}$ \\\\\n\\midrule\n" + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}\n")


def tab_term(cfg: dict[str, Any], res: dict[str, Any]) -> str:
    sc, H = cfg["lp"]["scale_bn"], cfg["lp"]["primary_horizon"]
    body = []
    for y, recs in res["term"].items():
        r = _h(recs, H)
        body.append(f"{TENOR_NAMES[y]} & {_cell(r, 'pre', sc)} & {_cell(r, 'post', sc)} & {_cell(r, 'diff', sc, True)} & "
                    f"{pval(r.diff_p)} \\\\")
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrrrr}\n\\toprule\n"
            "Tenor & Pre $\\beta_{10}$ & Post & $\\delta_{10}$ & $p$ \\\\\n\\midrule\n" + "\n".join(body) +
            "\n\\bottomrule\n\\end{tabular}\n")


def tab_asym(cfg: dict[str, Any], res: dict[str, Any]) -> str:
    an = cfg["lp"]["anchor_scale_bn"]
    body = []
    for reg, R in (("pre", "Pre"), ("post", "Post")):
        for h in (5, 10, 20):
            a = _h(res["asymmetry"], h)
            body.append(f"{R if h == 5 else ''} & {h} & {num(a[f'pos_{reg}'] * an, 1, True)} ({pval(a[f'pos_{reg}_p'])}) & "
                        f"{num(-a[f'neg_{reg}'] * an, 1, True)} ({pval(a[f'neg_{reg}_p'])}) & {pval(a[f'asym_{reg}_p'])} \\\\")
        if reg == "pre":
            body.append("\\midrule")
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrrrr}\n\\toprule\n"
            "Regime & $h$ & Inflow ($p$) & Outflow ($p$) & $p(\\beta^-{=}\\beta^+)$ \\\\\n\\midrule\n" + "\n".join(body) +
            "\n\\bottomrule\n\\end{tabular}\n")


def tab_stats(stats: pd.DataFrame) -> str:
    st = stats.set_index(["regime", "variable"])
    labels = {"5-day flow, primary (USD bn)": "5-day flow $F_t$ (USD bn)",
              "Primary supply (USD bn)": "Supply $S_t$ (USD bn)",
              "3-month bill (bp)": "3-month bill yield (bp)",
              "Daily change 3-month bill (bp)": "Daily $\\Delta$ 3-month yield (bp)",
              "2-year CMT (bp)": "2-year CMT yield (bp)", "VIX": "VIX", "ON RRP (USD bn)": "ON RRP (USD bn)"}
    body = []
    for v, lab in labels.items():
        cells = [f"{num(st.loc[(r, v), 'mean'], 2)} ({num(st.loc[(r, v), 'sd'], 2)})" for r in ("pre", "post")]
        body.append(f"{lab} & {cells[0]} & {cells[1]} \\\\")
    n = [int(st.loc[(r, '3-month bill (bp)'), 'N']) for r in ("pre", "post")]
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrr}\n\\toprule\n"
            f" & Pre ($N={n[0]}$) & Post ($N={n[1]}$) \\\\\n\\midrule\n" + "\n".join(body) +
            "\n\\bottomrule\n\\end{tabular}\n")


def tab_universe(cfg: dict[str, Any], meta: dict[str, Any]) -> str:
    coins = pd.read_parquet(ROOT / cfg["paths"]["processed"] / "coins_daily.parquet")
    end = pd.Timestamp(meta["panel_end"])
    last = coins[coins.index <= end].ffill().iloc[-1]
    body = [f"{c} & {i} & {meta['defillama_first_snapshot'][c]} & {num(last[c], 2) if pd.notna(last[c]) and last[c] > 0.005 else '--'} \\\\"
            for c, i in meta["defillama_ids"].items()]
    return ("% generated by src/viz/paper_tex.py\n\\begin{tabular}{lrrr}\n\\toprule\n"
            f"Coin & DefiLlama id & First snapshot & Supply {end:%d %b %Y} (USD bn) \\\\\n\\midrule\n" + "\n".join(body) +
            "\n\\bottomrule\n\\end{tabular}\n")


def make_paper_tex(cfg: dict[str, Any], panel: pd.DataFrame) -> None:
    tables = ROOT / cfg["paths"]["tables"]
    res = json.loads((tables / "lp_results.json").read_text())
    stats = pd.read_csv(tables / "summary_stats.csv")
    meta = json.loads((ROOT / cfg["paths"]["processed"] / "meta.json").read_text())
    (PAPER / "tables").mkdir(parents=True, exist_ok=True)
    write_numbers(numbers(cfg, res, stats, meta, panel), PAPER / "numbers.tex")
    for name, text in (("primary", tab_primary(cfg, res)), ("robustness", tab_robust(cfg, res)),
                       ("term", tab_term(cfg, res)), ("asymmetry", tab_asym(cfg, res)), ("stats", tab_stats(stats)),
                       ("universe", tab_universe(cfg, meta))):
        (PAPER / "tables" / f"{name}.tex").write_text(text)
    log.info("paper numbers and tables written to %s", PAPER)
