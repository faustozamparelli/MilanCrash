"""Shared statistical helpers used by the inference notebooks.

Every stochastic function defaults to `SEED = 42` so that repeated runs
across notebooks are reproducible. Pass a different seed explicitly if
a local context truly needs independent randomness.

The API intentionally mirrors the previously duplicated implementations
in:

- `notebooks/inference/Cerchie.ipynb`
- `notebooks/inference/CrashDrugUse.ipynb`
- `notebooks/inference/Fleet.ipynb`
- `notebooks/inference/CrashType.ipynb`

so notebook edits are a straightforward one-line import replacement.
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import lstsq
from statsmodels.stats.multitest import multipletests

SEED = 42


# ---------------------------------------------------------------------------
# Linear residualization helpers
# ---------------------------------------------------------------------------

def residualize_linear(y: pd.Series | np.ndarray, x: pd.Series | np.ndarray) -> np.ndarray:
    """Return residuals from OLS of y on [1, x]."""
    yy = pd.to_numeric(pd.Series(y), errors="coerce").to_numpy(dtype=float)
    xx = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(xx)), xx])
    beta = np.linalg.lstsq(X, yy, rcond=None)[0]
    return yy - X @ beta


def residualize_with_controls(
    y: np.ndarray,
    idx: np.ndarray,
    control_spec: Literal["trend_only", "trend_season"] = "trend_season",
) -> np.ndarray:
    """Residualize on a linear trend and (optionally) annual/semi-annual
    sinusoidal seasonality. `idx` is an integer month index."""
    t = idx.astype(float)
    if control_spec == "trend_only":
        X_ctrl = np.column_stack([np.ones_like(t), t])
    elif control_spec == "trend_season":
        X_ctrl = np.column_stack(
            [
                np.ones_like(t),
                t,
                np.sin(2 * np.pi * t / 12),
                np.cos(2 * np.pi * t / 12),
                np.sin(2 * np.pi * t / 6),
                np.cos(2 * np.pi * t / 6),
            ]
        )
    else:
        raise ValueError(f"unknown control_spec: {control_spec!r}")

    beta, *_ = lstsq(X_ctrl, y)
    return y - X_ctrl @ beta


# ---------------------------------------------------------------------------
# Permutation correlations
# ---------------------------------------------------------------------------

def _clean_pair(x: pd.Series | np.ndarray, y: pd.Series | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xx = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(dtype=float)
    yy = pd.to_numeric(pd.Series(y), errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(xx) & np.isfinite(yy)
    return xx[mask], yy[mask]


def perm_corr(
    x: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    method: Literal["pearson", "spearman"] = "pearson",
    n_perm: int = 12000,
    seed: int = SEED,
    min_obs: int = 5,
) -> tuple[float, float, int]:
    """Permutation correlation test. Returns (r, p_two_sided, n_obs).

    `p_two_sided = (count(|perm_r| >= |obs_r|) + 1) / (n_perm + 1)`.
    """
    xx, yy = _clean_pair(x, y)
    n_obs = int(len(xx))
    if n_obs < min_obs:
        return float("nan"), float("nan"), n_obs

    if method == "spearman":
        xx = pd.Series(xx).rank(method="average").to_numpy(dtype=float)
        yy = pd.Series(yy).rank(method="average").to_numpy(dtype=float)

    obs_r = float(np.corrcoef(xx, yy)[0, 1])

    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        perm_r = float(np.corrcoef(xx, rng.permutation(yy))[0, 1])
        if abs(perm_r) >= abs(obs_r):
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return obs_r, p_val, n_obs


def partial_corr_with_year(
    x: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    years: pd.Series | np.ndarray,
    method: Literal["pearson", "spearman"] = "pearson",
    n_perm: int = 12000,
    seed: int = SEED,
    min_obs: int = 5,
) -> tuple[float, float, int]:
    """Permutation partial correlation controlling for Year."""
    xx = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(dtype=float)
    yy = pd.to_numeric(pd.Series(y), errors="coerce").to_numpy(dtype=float)
    tt = pd.to_numeric(pd.Series(years), errors="coerce").to_numpy(dtype=float)

    mask = np.isfinite(xx) & np.isfinite(yy) & np.isfinite(tt)
    xx, yy, tt = xx[mask], yy[mask], tt[mask]

    n_obs = int(len(xx))
    if n_obs < min_obs:
        return float("nan"), float("nan"), n_obs

    rx = residualize_linear(xx, tt)
    ry = residualize_linear(yy, tt)

    if method == "spearman":
        rx = pd.Series(rx).rank(method="average").to_numpy(dtype=float)
        ry = pd.Series(ry).rank(method="average").to_numpy(dtype=float)

    obs_r = float(np.corrcoef(rx, ry)[0, 1])

    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        perm_r = float(np.corrcoef(rx, rng.permutation(ry))[0, 1])
        if abs(perm_r) >= abs(obs_r):
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return obs_r, p_val, n_obs


# ---------------------------------------------------------------------------
# Slope + bootstrap CI
# ---------------------------------------------------------------------------

def slope_perm_test(
    x: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    n_perm: int = 15000,
    seed: int = SEED,
) -> tuple[float, float]:
    """Permutation p-value on an OLS slope (x predicts y)."""
    xx, yy = _clean_pair(x, y)
    xx_c = xx - xx.mean()
    denom = float(np.sum(xx_c ** 2))
    obs_slope = float(np.sum(xx_c * (yy - yy.mean())) / denom)

    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        yp = rng.permutation(yy)
        slope_p = float(np.sum(xx_c * (yp - yp.mean())) / denom)
        if abs(slope_p) >= abs(obs_slope):
            count += 1
    p_val = (count + 1) / (n_perm + 1)
    return obs_slope, p_val


def bootstrap_slope_ci(
    x: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    n_boot: int = 5000,
    seed: int = SEED,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Pairwise-resample bootstrap CI for an OLS slope."""
    xx, yy = _clean_pair(x, y)
    rng = np.random.default_rng(seed)
    slopes: list[float] = []
    n = len(xx)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        xb = xx[idx]
        yb = yy[idx]
        xbc = xb - xb.mean()
        denom = float(np.sum(xbc ** 2))
        if denom == 0:
            continue
        slopes.append(float(np.sum(xbc * (yb - yb.mean())) / denom))

    if not slopes:
        return float("nan"), float("nan")
    return (
        float(np.quantile(slopes, alpha / 2)),
        float(np.quantile(slopes, 1 - alpha / 2)),
    )


def bootstrap_rate_ci(
    numerator: pd.Series | np.ndarray,
    denominator: pd.Series | np.ndarray,
    scale: float = 1.0,
    n_boot: int = 4000,
    seed: int = SEED,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap CI for `scale * sum(num) / sum(den)` rates."""
    num = pd.to_numeric(pd.Series(numerator), errors="coerce").to_numpy(dtype=float)
    den = pd.to_numeric(pd.Series(denominator), errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(num) & np.isfinite(den) & (den > 0)
    num = num[mask]
    den = den[mask]
    if len(num) < 3:
        return float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    idx = np.arange(len(num))
    boots: list[float] = []
    for _ in range(n_boot):
        b = rng.choice(idx, size=len(idx), replace=True)
        den_sum = den[b].sum()
        if den_sum <= 0:
            continue
        boots.append(scale * num[b].sum() / den_sum)

    if not boots:
        return float("nan"), float("nan")
    return (
        float(np.quantile(boots, alpha / 2)),
        float(np.quantile(boots, 1 - alpha / 2)),
    )


def bootstrap_corr_ci(
    x: np.ndarray,
    y: np.ndarray,
    method: Literal["spearman", "pearson"] = "spearman",
    n_boot: int = 600,
    seed: int = SEED,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap CI for a Spearman or Pearson correlation."""
    rng = np.random.default_rng(seed)
    idx = np.arange(len(x))
    boots: list[float] = []
    for _ in range(n_boot):
        sample_idx = rng.choice(idx, size=len(idx), replace=True)
        if method == "spearman":
            r, _ = stats.spearmanr(x[sample_idx], y[sample_idx])
        else:
            r = float(np.corrcoef(x[sample_idx], y[sample_idx])[0, 1])
        if np.isfinite(r):
            boots.append(float(r))
    if len(boots) == 0:
        return float("nan"), float("nan")
    return (
        float(np.quantile(boots, alpha / 2)),
        float(np.quantile(boots, 1 - alpha / 2)),
    )


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def cramers_v(table: pd.DataFrame) -> float:
    """Cramér's V association effect size for a contingency table."""
    chi2 = stats.chi2_contingency(table)[0]
    n = table.values.sum()
    r, k = table.shape
    if n == 0 or min(k - 1, r - 1) == 0:
        return float("nan")
    return float(np.sqrt((chi2 / n) / min(k - 1, r - 1)))


def bh_qvalues(pvals: pd.Series | np.ndarray) -> np.ndarray:
    """Benjamini–Hochberg q-values (FDR). NaNs are preserved."""
    p = np.asarray(pvals, dtype=float)
    mask = np.isfinite(p)
    q = np.full_like(p, np.nan, dtype=float)
    if mask.any():
        q[mask] = multipletests(p[mask], method="fdr_bh")[1]
    return q
