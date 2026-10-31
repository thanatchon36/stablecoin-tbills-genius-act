"""Align stablecoin supply, yields and controls on the US business-day calendar.

Timing convention: a DefiLlama snapshot dated d (00:00 UTC) is the supply at the end of US day d-1,
so the supply for business day t is the snapshot dated t+1 (`shift_days=1`). `shift_days=0` is the
pre-registered 1-day-timing robustness variant.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

YIELD_COLS = ["DTB4WK", "DTB3", "DTB6", "DGS1", "DGS2", "DGS1MO", "DGS3MO", "EFFR", "IORB"]
LEVEL_CONTROLS = ["VIXCLS", "SP500", "RRPONTSYD", "DTWEXBGS"]


def clean_coin(s: pd.Series, max_ffill: int) -> tuple[pd.Series, dict[str, int]]:
    """Put one coin on a daily calendar between its first and last observation.

    Gaps of <= max_ffill days are forward-filled; longer gaps stay NaN. Returns the series and gap counts.
    """
    s = s.dropna()
    full = s.reindex(pd.date_range(s.index[0], s.index[-1], freq="D"))
    miss = full.isna()
    run_id = (~miss).cumsum()
    run_len = miss.groupby(run_id).transform("sum").where(miss, 0)
    filled = full.ffill().where(~miss | (run_len <= max_ffill))
    stats = {"missing_days": int(miss.sum()), "ffilled_days": int((miss & (run_len <= max_ffill)).sum()),
             "nan_days": int(filled.isna().sum())}
    return filled, stats


def aggregate(coins: pd.DataFrame, max_ffill: int) -> tuple[pd.Series, pd.DataFrame]:
    """Sum coins on a daily calendar. A coin contributes 0 before its first observation and is
    excluded (contributes 0) on dates inside a gap longer than `max_ffill` days (logged)."""
    cleaned, stats = {}, {}
    for c in coins:
        cleaned[c], stats[c] = clean_coin(coins[c], max_ffill)
        if stats[c]["missing_days"]:
            log.info("coin %s gaps: %s", c, stats[c])
    idx = pd.date_range(min(s.index[0] for s in cleaned.values()), max(s.index[-1] for s in cleaned.values()), freq="D")
    wide = pd.DataFrame({c: s.reindex(idx) for c, s in cleaned.items()})
    inside = pd.DataFrame({c: (idx >= s.index[0]) & (idx <= s.index[-1]) for c, s in cleaned.items()}, index=idx)
    for c in wide:
        excl = wide[c].isna() & inside[c]
        if excl.any():
            log.warning("coin %s excluded from aggregate on %d days (%s to %s)", c, int(excl.sum()),
                        excl[excl].index[0].date(), excl[excl].index[-1].date())
    total = wide.fillna(0.0).sum(axis=1)
    return total, pd.DataFrame(stats).T


def to_us_day(s: pd.Series, shift_days: int) -> pd.Series:
    """Re-date snapshot-dated supply to the US day it measures (end of day d - shift_days)."""
    out = s.copy()
    out.index = out.index - pd.Timedelta(days=shift_days)
    return out


def on_calendar(s: pd.Series, cal: pd.DatetimeIndex, max_ffill: int = 3) -> pd.Series:
    """Latest observation at or before each business day, if it is at most `max_ffill` business days stale."""
    s = s.dropna()
    s = s[~s.index.duplicated()]
    union = s.index.union(cal)
    vals = s.reindex(union).ffill().reindex(cal)
    last_obs = pd.Series(s.index, index=s.index).reindex(union).ffill().reindex(cal)
    stale = np.arange(len(cal)) - cal.searchsorted(last_obs.fillna(cal[0] - pd.Timedelta(days=1)).values)
    return vals.where(last_obs.notna().values & (stale <= max_ffill))


def build_panel(coins: pd.DataFrame, allusd: pd.Series, fred: pd.DataFrame, btc: pd.Series,
                cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (business-day panel, daily per-coin supply in US-day dating, coin gap stats)."""
    max_ffill = cfg["defillama"]["max_ffill_days"]
    primary, gap_stats = aggregate(coins, max_ffill)
    supplies: dict[str, pd.Series] = {
        "S_primary": primary,
        "S_USDT": clean_coin(coins["USDT"], max_ffill)[0],
        "S_USDC": clean_coin(coins["USDC"], max_ffill)[0],
        "S_allusd": clean_coin(allusd, max_ffill)[0],
    }
    cal = fred["DTB3"].dropna().index
    first_supply = to_us_day(primary.dropna(), 1).index[0]
    cal = cal[(cal >= first_supply) & (cal <= to_us_day(primary.dropna(), 1).index[-1])]

    panel = pd.DataFrame(index=cal)
    panel.index.name = "date"
    for name, s in supplies.items():
        panel[name] = to_us_day(s, 1).reindex(cal)            # baseline timing
        panel[name + "_t0"] = to_us_day(s, 0).reindex(cal)    # 1-day timing shift
    for c in YIELD_COLS:
        panel[c] = on_calendar(fred[c], cal) * 100.0           # percent -> bp
    for c in LEVEL_CONTROLS:
        panel[c] = on_calendar(fred[c], cal)
    panel["BTC"] = btc.reindex(cal)
    panel["Post"] = (panel.index >= pd.Timestamp(cfg["breaks"]["primary"])).astype(int)

    daily_coins = pd.DataFrame({c: to_us_day(clean_coin(coins[c], max_ffill)[0], 1) for c in coins})
    log.info("panel: %s to %s, %d business days", cal[0].date(), cal[-1].date(), len(cal))
    return panel, daily_coins, gap_stats


def nan_report(panel: pd.DataFrame, start: str) -> pd.Series:
    """Share of NaNs per column in the estimation sample."""
    p = panel[panel.index >= pd.Timestamp(start)]
    return p.isna().mean().sort_values(ascending=False)


def summary_stats(panel: pd.DataFrame, start: str, k: int = 5) -> pd.DataFrame:
    """Summary statistics of key variables, pre/post, in the estimation sample."""
    p = panel.copy()  # flows/changes before truncation, so N matches the regression sample
    p["F5"] = p["S_primary"] - p["S_primary"].shift(k)
    p["dDTB3"] = p["DTB3"].diff()
    p = p[p.index >= pd.Timestamp(start)]
    cols = {"F5": "5-day flow, primary (USD bn)", "S_primary": "Primary supply (USD bn)",
            "DTB3": "3-month bill (bp)", "dDTB3": "Daily change 3-month bill (bp)",
            "DGS2": "2-year CMT (bp)", "VIXCLS": "VIX", "RRPONTSYD": "ON RRP (USD bn)"}
    rows = []
    for regime, sub in [("full", p), ("pre", p[p.Post == 0]), ("post", p[p.Post == 1])]:
        for c, label in cols.items():
            x = sub[c].dropna()
            rows.append({"regime": regime, "variable": label, "N": len(x), "mean": x.mean(), "sd": x.std(),
                         "min": x.min(), "max": x.max()})
    return pd.DataFrame(rows)

