"""Orchestrate the project: fetch -> build -> estimate -> figures -> tables. Idempotent.

Usage: python -m src.pipeline {fetch,build,estimate,figures,tables,all} [--refresh]
`--refresh` re-downloads raw data; otherwise the newest cached raw files in data/raw/ are reused.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

import pandas as pd

from src.data.build_panel import build_panel, nan_report, summary_stats
from src.data.fetch_crypto import fetch_btc
from src.data.fetch_defillama import fetch_supply
from src.data.fetch_fred import fetch_fred
from src.utils import ROOT, fetch_timestamp, latest_cached, load_config, setup_logging

log = logging.getLogger("pipeline")


def step_fetch(cfg: dict[str, Any], refresh: bool) -> tuple[pd.DataFrame, pd.Series, dict[str, str], pd.DataFrame, pd.Series]:
    coins, allusd, ids = fetch_supply(cfg, refresh)
    return coins, allusd, ids, fetch_fred(cfg, refresh), fetch_btc(cfg, refresh)


def step_build(cfg: dict[str, Any], refresh: bool = False) -> None:
    """Fetch (or load cached) raw data, align, and write data/processed/."""
    coins, allusd, ids, fred, btc = step_fetch(cfg, refresh)
    panel, daily, gaps = build_panel(coins, allusd, fred, btc, cfg)
    out = ROOT / cfg["paths"]["processed"]
    out.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out / "panel.parquet")
    daily.to_parquet(out / "coins_daily.parquet")
    gaps.to_csv(out / "coin_gaps.csv")
    start = cfg["sample"]["estimation_start"]
    nans = nan_report(panel, start)
    stats = summary_stats(panel, start)
    stats.to_csv(ROOT / cfg["paths"]["tables"] / "summary_stats.csv", index=False)
    meta = {
        "defillama_ids": ids,
        "vintage_defillama_utc": fetch_timestamp(latest_cached(cfg, "defillama_USDT", "json.gz")).isoformat(),
        "vintage_fred_utc": fetch_timestamp(latest_cached(cfg, "fred_DTB3", "csv")).isoformat(),
        "vintage_binance_utc": fetch_timestamp(latest_cached(cfg, "binance_btcusdt", "json.gz")).isoformat(),
        "defillama_first_snapshot": {c: str(coins[c].first_valid_index().date()) for c in coins},
        "panel_start": str(panel.index[0].date()),
        "panel_end": str(panel.index[-1].date()),
        "estimation_start": start,
        "nan_share_estimation_sample": {k: round(float(v), 5) for k, v in nans.items()},
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    log.info("panel written: %s to %s; NaN shares (top): %s", meta["panel_start"], meta["panel_end"],
             nans.head(3).round(4).to_dict())


def load_panel(cfg: dict[str, Any]) -> pd.DataFrame:
    return pd.read_parquet(ROOT / cfg["paths"]["processed"] / "panel.parquet")


def main() -> None:
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fetch", "build", "estimate", "figures", "tables", "paper", "all"])
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    for d in ("raw", "processed", "figures", "tables"):
        (ROOT / cfg["paths"][d]).mkdir(parents=True, exist_ok=True)
    if a.step == "fetch":
        step_fetch(cfg, a.refresh)
    if a.step in ("build", "all"):
        step_build(cfg, a.refresh)
    if a.step in ("estimate", "all"):
        from src.analysis.robustness import run_all
        run_all(cfg, load_panel(cfg))
    if a.step in ("figures", "all"):
        from src.viz.figures import make_all
        make_all(cfg, load_panel(cfg))
    if a.step in ("tables", "all"):
        from src.viz.tables import make_tables
        make_tables(cfg)
    if a.step in ("paper", "all"):
        from src.viz.paper_figures import make_paper_figures
        from src.viz.paper_tex import make_paper_tex
        make_paper_figures(cfg, load_panel(cfg))
        make_paper_tex(cfg, load_panel(cfg))


if __name__ == "__main__":
    main()
