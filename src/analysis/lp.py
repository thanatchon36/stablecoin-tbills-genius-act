"""Jordà (2005) local projections with a regime break (see docs/PAP.md §4).

    y_{t+h} - y_{t-1} = a_h + b_h F_t + d_h F_t*Post_t + g_h Post_t + G_h' X_t + e_{t+h}

All coefficients are per USD 1 bn of flow and in basis points; scaling happens in tables/figures.
Inference: Newey-West HAC (Bartlett), maxlags = h + 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


@dataclass(frozen=True)
class Spec:
    """One LP specification. Defaults are the pre-registered primary spec."""

    outcome: str = "DTB3"            # panel column (bp); "SPREAD_DTB3_EFFR" is built on the fly
    supply: str = "S_primary"        # supply column (USD bn); "_t0" suffix = 1-day timing shift
    k: int = 5                       # flow window (business days)
    n_lags: int = 5
    contemporaneous: bool = True     # include ΔDGS2, ΔVIX, BTC, S&P, Δlog(RRP+1)
    break_date: str = "2025-07-18"
    start: str = "2021-01-04"
    end: str | None = None           # truncate the panel BEFORE building leads (placebo)
    drop_windows: tuple[tuple[str, int], ...] = field(default=())  # (event date, ±business days)
    asymmetric: bool = False


def outcome_series(panel: pd.DataFrame, outcome: str) -> pd.Series:
    if outcome == "SPREAD_DTB3_EFFR":
        return panel["DTB3"] - panel["EFFR"]
    return panel[outcome]


def build_design(panel: pd.DataFrame, spec: Spec) -> tuple[pd.Series, pd.DataFrame]:
    """Return (y level series, regressor DataFrame) on the full calendar, before sample selection."""
    p = panel if spec.end is None else panel[panel.index <= pd.Timestamp(spec.end)]
    y = outcome_series(p, spec.outcome)
    s = p[spec.supply]
    flow = s - s.shift(spec.k)
    daily = s.diff()
    post = (p.index >= pd.Timestamp(spec.break_date)).astype(float)
    X = pd.DataFrame(index=p.index)
    if spec.asymmetric:
        X["Fpos"], X["Fneg"] = flow.clip(lower=0), flow.clip(upper=0)
        X["Fpos_x_Post"], X["Fneg_x_Post"] = X["Fpos"] * post, X["Fneg"] * post
    else:
        X["F"] = flow
        X["F_x_Post"] = flow * post
    X["Post"] = post
    dy = y.diff()
    for j in range(1, spec.n_lags + 1):
        X[f"dy_l{j}"] = dy.shift(j)
        X[f"f_l{j}"] = daily.shift(j)
    if spec.contemporaneous:
        if spec.outcome != "DGS2":
            X["dDGS2"] = p["DGS2"].diff()
        X["dVIX"] = p["VIXCLS"].diff()
        X["ret_BTC"] = 100 * np.log(p["BTC"]).diff()
        X["ret_SPX"] = 100 * np.log(p["SP500"]).diff()
        X["dlogRRP"] = 100 * np.log(p["RRPONTSYD"] + 1.0).diff()
    return y, X


def _sample_mask(index: pd.DatetimeIndex, spec: Spec) -> np.ndarray:
    keep = index >= pd.Timestamp(spec.start)
    for date, w in spec.drop_windows:
        pos = index.searchsorted(pd.Timestamp(date))
        lo, hi = max(pos - w, 0), min(pos + w, len(index) - 1)
        keep &= ~((index >= index[lo]) & (index <= index[hi]))
    return keep


def _lincomb(params: pd.Series, cov: pd.DataFrame, names: list[str], signs: list[float]) -> tuple[float, float]:
    w = pd.Series(signs, index=names)
    est = float((params[names] * w).sum())
    se = float(np.sqrt(w @ cov.loc[names, names] @ w))
    return est, se


def _p(est: float, se: float) -> float:
    return float(2 * stats.norm.sf(abs(est / se))) if se > 0 else float("nan")


def estimate_h(y: pd.Series, X: pd.DataFrame, h: int, spec: Spec) -> dict[str, float]:
    """Estimate one horizon and return the reported quantities."""
    lhs = (y.shift(-h) - y.shift(1)).rename("lhs")
    df = pd.concat([lhs, X], axis=1)[_sample_mask(X.index, spec)].dropna()
    res = sm.OLS(df["lhs"], sm.add_constant(df.drop(columns="lhs"))).fit(
        cov_type="HAC", cov_kwds={"maxlags": h + 1})
    b, V = res.params, res.cov_params()
    out: dict[str, float] = {"h": h, "N": int(res.nobs), "N_pre": int((df["Post"] == 0).sum()),
                             "N_post": int((df["Post"] == 1).sum()),
                             "start": str(df.index[0].date()), "end": str(df.index[-1].date())}
    if spec.asymmetric:
        for side in ("pos", "neg"):
            pre = (float(b[f"F{side}"]), float(np.sqrt(V.loc[f"F{side}", f"F{side}"])))
            post = _lincomb(b, V, [f"F{side}", f"F{side}_x_Post"], [1, 1])
            diff = (float(b[f"F{side}_x_Post"]), float(np.sqrt(V.loc[f"F{side}_x_Post", f"F{side}_x_Post"])))
            for tag, (e, s) in {"pre": pre, "post": post, "diff": diff}.items():
                out[f"{side}_{tag}"], out[f"{side}_{tag}_se"], out[f"{side}_{tag}_p"] = e, s, _p(e, s)
        # Wald test beta_neg == beta_pos within each regime
        for tag, names, signs in [("pre", ["Fneg", "Fpos"], [1, -1]),
                                  ("post", ["Fneg", "Fneg_x_Post", "Fpos", "Fpos_x_Post"], [1, 1, -1, -1])]:
            e, s = _lincomb(b, V, names, signs)
            out[f"asym_{tag}"], out[f"asym_{tag}_se"], out[f"asym_{tag}_p"] = e, s, _p(e, s)
    else:
        pre = (float(b["F"]), float(np.sqrt(V.loc["F", "F"])))
        post = _lincomb(b, V, ["F", "F_x_Post"], [1, 1])
        diff = (float(b["F_x_Post"]), float(np.sqrt(V.loc["F_x_Post", "F_x_Post"])))
        for tag, (e, s) in {"pre": pre, "post": post, "diff": diff}.items():
            out[tag], out[f"{tag}_se"], out[f"{tag}_p"] = e, s, _p(e, s)
    return out


def run_lp(panel: pd.DataFrame, spec: Spec, horizons: range) -> pd.DataFrame:
    """Estimate all horizons for one spec."""
    y, X = build_design(panel, spec)
    return pd.DataFrame([estimate_h(y, X, h, spec) for h in horizons])


def flow_sd(panel: pd.DataFrame, spec: Spec) -> float:
    """Standard deviation of F over the estimation sample (for per-1-s.d. scaling)."""
    s = panel[spec.supply]
    f = (s - s.shift(spec.k))[panel.index >= pd.Timestamp(spec.start)]
    return float(f.std())
