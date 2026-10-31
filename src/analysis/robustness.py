"""Run every pre-registered specification (PAP §4–6) and write output/tables/lp_results.json."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, replace
from typing import Any

import pandas as pd

from src.analysis.lp import Spec, flow_sd, run_lp
from src.utils import ROOT

log = logging.getLogger(__name__)


def robustness_specs(cfg: dict[str, Any], base: Spec) -> dict[str, Spec]:
    """The pre-registered robustness list (PAP §6), in table order."""
    b, ev = cfg["breaks"], cfg["events"]
    w = cfg["lp"]["event_window_bdays"]
    return {
        "Baseline (primary spec)": base,
        "Alternative break 2025-06-17 (Senate)": replace(base, break_date=b["alternative"]),
        "Placebo break 2024-07-18 (data to 2025-06-16)": replace(base, break_date=b["placebo"],
                                                                end=b["placebo_sample_end"]),
        "Drop ±10 bdays around Terra, FTX, SVB": replace(base, drop_windows=tuple((ev[e], w) for e in ("terra", "ftx", "svb"))),
        "USDT-only flows": replace(base, supply="S_USDT"),
        "USDC-only flows": replace(base, supply="S_USDC"),
        "All USD-pegged aggregate": replace(base, supply="S_allusd"),
        "1-day timing shift": replace(base, supply="S_primary_t0"),
        "Flow window k = 1": replace(base, k=1),
        "Flow window k = 10": replace(base, k=10),
        "Lags-only controls": replace(base, contemporaneous=False),
    }


def outflow_counts(panel: pd.DataFrame, spec: Spec) -> dict[str, int]:
    """Descriptive: number of business days with a negative 5-day flow, by regime and in 2022-23."""
    p = panel[panel.index >= pd.Timestamp(spec.start)]
    f = (panel[spec.supply] - panel[spec.supply].shift(spec.k)).reindex(p.index)
    neg = f < 0
    pre = p["Post"] == 0
    return {"pre": int((neg & pre).sum()), "post": int((neg & ~pre).sum()),
            "pre_2022_2023": int((neg & pre & p.index.year.isin([2022, 2023])).sum()),
            "N_pre": int(pre.sum()), "N_post": int((~pre).sum())}


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(df.to_json(orient="records"))


def run_all(cfg: dict[str, Any], panel: pd.DataFrame) -> dict[str, Any]:
    lp = cfg["lp"]
    H = range(lp["horizons"] + 1)
    base = Spec(outcome=lp["primary_outcome"], k=lp["flow_window"], n_lags=lp["n_lags"],
                break_date=cfg["breaks"]["primary"], start=cfg["sample"]["estimation_start"])
    out: dict[str, Any] = {"spec": asdict(base), "flow_sd_bn": flow_sd(panel, base),
                           "outflow_days": outflow_counts(panel, base)}

    log.info("primary LP (DTB3), h=0..%d", lp["horizons"])
    out["primary"] = _records(run_lp(panel, base, H))
    out["primary_lags_only"] = _records(run_lp(panel, replace(base, contemporaneous=False), H))

    out["term"] = {}
    for y in lp["term_outcomes"]:
        log.info("term structure: %s", y)
        out["term"][y] = _records(run_lp(panel, replace(base, outcome=y), H))

    log.info("asymmetry")
    out["asymmetry"] = _records(run_lp(panel, replace(base, asymmetric=True), H))
    log.info("spread outcome DTB3-EFFR")
    out["spread"] = _records(run_lp(panel, replace(base, outcome="SPREAD_DTB3_EFFR"), H))

    h10 = range(lp["primary_horizon"], lp["primary_horizon"] + 1)
    out["robustness"] = {}
    for name, spec in robustness_specs(cfg, base).items():
        log.info("robustness: %s", name)
        r = _records(run_lp(panel, spec, h10))[0]
        r["flow_sd_bn"] = flow_sd(panel, spec)
        out["robustness"][name] = r

    path = ROOT / cfg["paths"]["tables"] / "lp_results.json"
    path.write_text(json.dumps(out, indent=1))
    log.info("results written: %s", path)
    return out
