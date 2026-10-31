"""Data-sanity tests. They must pass before any regression is run (`make test` precedes `make estimate`)."""

from __future__ import annotations

import json
import logging

import pandas as pd
import pytest

from src.utils import ROOT, load_config

log = logging.getLogger(__name__)
CFG = load_config()
PROC = ROOT / CFG["paths"]["processed"]
START = pd.Timestamp(CFG["sample"]["estimation_start"])
OUTCOMES = ["DTB4WK", "DTB3", "DTB6", "DGS1", "DGS2", "EFFR"]
USED = ["S_primary", "S_primary_t0", "S_USDT", "S_USDC", "S_allusd", *OUTCOMES, "VIXCLS", "SP500", "RRPONTSYD", "BTC"]

# One externally reported supply figure per major coin: Ahmed & Aldasoro (2025, rev. June 2026), fn. 16,
# "USDT and USDC account for approximately $184B and $80B respectively" as of March 2026 (CoinMarketCap).
WEB_REF = {"S_USDT": ("2026-03-31", 184.0), "S_USDC": ("2026-03-31", 80.0)}


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(PROC / "panel.parquet")


@pytest.fixture(scope="module")
def meta() -> dict:
    return json.loads((PROC / "meta.json").read_text())


def test_dates_unique_and_monotone(panel: pd.DataFrame) -> None:
    assert not panel.index.duplicated().any()
    assert panel.index.is_monotonic_increasing


def test_latest_observation_fresh(panel: pd.DataFrame, meta: dict) -> None:
    """Latest observation is <= 7 days older than the data vintage (fetch time), not 'today',
    so the test stays valid when the committed vintage is re-run later."""
    vintage = pd.Timestamp(meta["vintage_fred_utc"]).tz_convert(None)
    assert (vintage - panel.index[-1]).days <= 7


def test_supply_positive_every_coin() -> None:
    coins = pd.read_parquet(PROC / "coins_daily.parquet")
    for c in coins:
        vals = coins[c].dropna()
        assert (vals > 0).all(), f"{c} has non-positive supply"


def test_yields_in_range(panel: pd.DataFrame) -> None:
    p = panel[panel.index >= START]
    for c in OUTCOMES:
        x = p[c].dropna()
        assert x.between(0, 700).all(), f"{c} outside 0-7%: {x.min()}..{x.max()}"


def test_nan_share_after_alignment(panel: pd.DataFrame) -> None:
    p = panel[panel.index >= START]
    shares = p[USED].isna().mean()
    log.info("NaN shares in estimation sample:\n%s", shares.round(4).to_string())
    print("\nNaN shares:", shares.round(4).to_dict())
    assert (shares < 0.02).all(), shares[shares >= 0.02]


def test_n_pre_post_printed(panel: pd.DataFrame) -> None:
    p = panel[panel.index >= START]
    n_pre, n_post = int((p.Post == 0).sum()), int((p.Post == 1).sum())
    print(f"\nN_pre={n_pre} N_post={n_post} (business days in estimation sample)")
    assert n_pre > 0 and n_post > 0


@pytest.mark.parametrize("col", list(WEB_REF))
def test_supply_matches_external_reference(panel: pd.DataFrame, col: str) -> None:
    date, ref = WEB_REF[col]
    ours = panel[col].asof(pd.Timestamp(date))
    assert abs(ours / ref - 1) <= 0.30, f"{col} {ours:.1f} vs reference {ref}"
