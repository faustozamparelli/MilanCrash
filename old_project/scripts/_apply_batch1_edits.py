"""Batch 1 edits for the inference notebooks.

This script performs *structural* and *code* edits on the four notebooks
in `notebooks/inference/`:

- Cerchie: fix Poisson reference, print Wald chi-square, split the
  dense per-km2 tables cell into four focused cells.
- CrashDrugUse: add Spearman columns, post-hoc power table, broader LOO.
- Fleet: bootstrap CI on post-2020 interaction, extend regime test to
  car_share and heavy_goods_share, generalize rolling-window plot.
- CrashType: control for month/year in severity GLMs, stratify the
  pairplot sample, drop share_3plus from regression features.

Also unifies random seeds to a single module-level `SEED = 42` per
notebook.

After running this script, re-run `_add_inference_markdown.py` with the
updated explainer map, then execute each notebook with
`jupyter nbconvert --execute --inplace`.

Idempotent: all changes replace whole cell sources rather than edit in
place, so re-running gives the same result.
"""
from __future__ import annotations

import json
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFERENCE = ROOT / "notebooks" / "inference"

AUTO_MARKER = "<!-- auto-explainer:v1 -->"


def _src_to_lines(src: str) -> list[str]:
    return src.splitlines(keepends=True)


def _strip_auto_markers(cells: list[dict]) -> list[dict]:
    kept = []
    for c in cells:
        if c.get("cell_type") == "markdown":
            s = c.get("source", "")
            if isinstance(s, list):
                s = "".join(s)
            if s.strip().startswith(AUTO_MARKER):
                continue
        kept.append(c)
    return kept


def _empty_code_cell(source: str, metadata: dict | None = None) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata or {},
        "outputs": [],
        "source": _src_to_lines(source),
    }


def load(name: str) -> dict:
    with (INFERENCE / name).open() as f:
        return json.load(f)


def save(name: str, nb: dict) -> None:
    with (INFERENCE / name).open("w") as f:
        json.dump(nb, f, indent=1)
        f.write("\n")


# ---------------------------------------------------------------------------
# Cerchie.ipynb
# ---------------------------------------------------------------------------

CERCHIE_CELL_0 = '''\
from pathlib import Path
import sys

import pandas as pd

# Reproducibility seed used by every stochastic helper in this notebook.
SEED = 42

# Resolve the processed data directory whether the kernel starts in project root or notebooks/.
candidate_roots = [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]
processed_dir = None
for root in candidate_roots:
    candidate = root / "data" / "processed"
    if candidate.exists():
        processed_dir = candidate
        project_root = root
        break

if processed_dir is None:
    raise FileNotFoundError("Could not find data/processed from the current working directory.")

# Make the shared inference utilities importable.
scripts_dir = str(project_root / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from inference_utils import bootstrap_rate_ci, bh_qvalues  # noqa: E402

monthly = pd.read_csv(processed_dir / "milan_crashes_monthly_cleaned.csv")
rings = pd.read_csv(processed_dir / "milan_crashes_monthly_city_ring_cleaned.csv")

monthly_check = (
    monthly.assign(
        year=monthly["Anno"].astype(int),
        month=monthly["Mese"].astype(int),
        monthly_total_crashes=monthly["IncidentiMortali"] + monthly["IncidentiSoliFeriti"],
    )
    .groupby(["year", "month"], as_index=False)["monthly_total_crashes"]
    .sum(min_count=1)
)

rings_check = (
    rings.assign(
        year=rings["Anno"].astype(int),
        month=rings["Mese"].astype(int),
    )
    .groupby(["year", "month"], as_index=False)["Incidenti"]
    .sum(min_count=1)
    .rename(columns={"Incidenti": "rings_total_crashes"})
)

comparison = (
    monthly_check.merge(rings_check, on=["year", "month"], how="outer")
    .sort_values(["year", "month"])
    .reset_index(drop=True)
)
comparison["delta"] = comparison["monthly_total_crashes"] - comparison["rings_total_crashes"]
comparison["has_missing"] = comparison["monthly_total_crashes"].isna() | comparison[
    "rings_total_crashes"
].isna()
comparison["is_match"] = (~comparison["has_missing"]) & comparison["delta"].eq(0)

numeric_abs_delta = comparison.loc[comparison["delta"].notna(), "delta"].abs()
summary = pd.Series(
    {
        "year_month_pairs_in_monthly": int(monthly_check.shape[0]),
        "year_month_pairs_in_rings": int(rings_check.shape[0]),
        "year_month_pairs_compared": int(comparison.shape[0]),
        "all_year_month_pairs_match": bool(comparison["is_match"].all()),
        "mismatched_pairs": int((~comparison["is_match"]).sum()),
        "mismatches_due_to_missing_values": int(comparison["has_missing"].sum()),
        "max_abs_delta_non_missing": int(numeric_abs_delta.max()) if not numeric_abs_delta.empty else 0,
    }
)

display(summary.to_frame("value"))

coverage_by_year = (
    comparison.assign(
        present_in_both=comparison["monthly_total_crashes"].notna()
        & comparison["rings_total_crashes"].notna()
    )
    .groupby("year", as_index=False)["present_in_both"]
    .sum()
    .rename(columns={"present_in_both": "months_present_in_both"})
)
coverage_by_year["expected_months"] = 12
coverage_by_year["all_12_months_present"] = coverage_by_year["months_present_in_both"].eq(12)

display(coverage_by_year)

mismatches = comparison.loc[~comparison["is_match"]].copy()
if mismatches.empty:
    print(
        "All year-month pairs match: total crashes in monthly dataset equal summed city-ring crashes for every month of every year."
    )
else:
    print(f"{len(mismatches)} mismatched year-month pair(s) found.")
    display(mismatches.head(20))
'''


# Split the original cell 2 into four focused sub-cells (2a, 2b, 2c, 2d).

CERCHIE_CELL_2A = '''\
# 2a. Area table + ring metrics build
import pandas as pd

required_columns = {"year", "month", "monthly_total_crashes", "rings_total_crashes", "has_missing"}
if "comparison" not in globals() or not required_columns.issubset(set(comparison.columns)):
    raise ValueError("Run the consistency-check cell first to build the comparison dataframe.")

ring_metrics = rings.copy()
ring_metrics["year"] = ring_metrics["Anno"].astype(int)
ring_metrics["month"] = ring_metrics["Mese"].astype(int)
ring_metrics["total_incidents"] = ring_metrics["Incidenti"].astype(float)
ring_metrics["fatal_incidents"] = ring_metrics["Morti"].astype(float)
ring_metrics["non_fatal_proxy"] = ring_metrics["Feriti"].astype(float)

area_by_cerchia = pd.DataFrame(
    [
        {"Cerchia": "Entro la Cerchia dei Navigli", "area_km2": 2.97, "notes": "confirmed"},
        {"Cerchia": "Dalla Cerchia dei Navigli alle Mura Spagnole", "area_km2": 6.70, "notes": "confirmed"},
        {"Cerchia": "Dalle Mura Spagnole alla Nuova Circonvallazione", "area_km2": 21.33, "notes": "approximation"},
        {"Cerchia": "Dalla Nuova Circonvallazione ai confini del Comune", "area_km2": 150.84, "notes": "approximation"},
    ]
)

print("Area table used for normalization (km2):")
display(area_by_cerchia)

ring_metrics = ring_metrics.merge(area_by_cerchia[["Cerchia", "area_km2"]], on="Cerchia", how="left")

excluded_cerchie = sorted(ring_metrics.loc[ring_metrics["area_km2"].isna(), "Cerchia"].dropna().unique())
if excluded_cerchie:
    print("Excluded from normalized cerchia outputs (missing area):")
    print(", ".join(excluded_cerchie))

ring_metrics_norm = ring_metrics.dropna(subset=["area_km2"]).copy()
for metric in ["fatal_incidents", "total_incidents", "non_fatal_proxy"]:
    ring_metrics_norm[f"{metric}_per_km2"] = ring_metrics_norm[metric] / ring_metrics_norm["area_km2"]

known_total_area_km2 = float(area_by_cerchia["area_km2"].sum())
'''


CERCHIE_CELL_2B = '''\
# 2b. Resolve monthly totals and surface fallback rows
comparison["resolved_total_crashes"] = comparison["monthly_total_crashes"].where(
    comparison["monthly_total_crashes"].notna(), comparison["rings_total_crashes"]
)

mismatch_fallbacks = comparison.loc[
    comparison["has_missing"], ["year", "month", "rings_total_crashes"]
].rename(columns={"rings_total_crashes": "fallback_total_from_rings"})
if not mismatch_fallbacks.empty:
    print("Using rings_total_crashes fallback for these year-month pairs:")
    display(mismatch_fallbacks.sort_values(["year", "month"]).reset_index(drop=True))
else:
    print("No fallback substitutions needed.")

month_labels = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
month_order = list(range(1, 13))
'''


CERCHIE_CELL_2C = '''\
# 2c. Per-metric density tables (Cerchia x Month)
def metric_numeric_tables(metric_density_col: str, metric_title: str) -> dict:
    avg_matrix = (
        ring_metrics_norm.groupby(["Cerchia", "month"], as_index=False)[metric_density_col]
        .mean()
        .pivot(index="Cerchia", columns="month", values=metric_density_col)
        .reindex(columns=month_order)
        .rename(columns=month_labels)
        .round(4)
    )

    diff_by_cerchia = pd.DataFrame(
        {
            "avg_across_months_per_km2": avg_matrix.mean(axis=1),
            "max_monthly_avg_per_km2": avg_matrix.max(axis=1),
            "min_monthly_avg_per_km2": avg_matrix.min(axis=1),
        }
    ).round(4)
    diff_by_cerchia["range_max_min_per_km2"] = (
        diff_by_cerchia["max_monthly_avg_per_km2"] - diff_by_cerchia["min_monthly_avg_per_km2"]
    ).round(4)
    diff_by_cerchia = diff_by_cerchia.sort_values("avg_across_months_per_km2", ascending=False)

    diff_by_month = pd.DataFrame(
        {
            "avg_across_cerchie_per_km2": avg_matrix.mean(axis=0),
            "max_cerchia_avg_per_km2": avg_matrix.max(axis=0),
            "min_cerchia_avg_per_km2": avg_matrix.min(axis=0),
        }
    ).round(4)
    diff_by_month["range_max_min_per_km2"] = (
        diff_by_month["max_cerchia_avg_per_km2"] - diff_by_month["min_cerchia_avg_per_km2"]
    ).round(4)
    diff_by_month = diff_by_month.sort_values("avg_across_cerchie_per_km2", ascending=False)

    top_cell_cerchia, top_cell_month = avg_matrix.stack().idxmax()
    top_cell_avg_value = float(avg_matrix.loc[top_cell_cerchia, top_cell_month])

    print(f"\\n{metric_title} - average values per km2 (Cerchia x Month)")
    display(avg_matrix)
    print(f"{metric_title} - differences by cerchia (per km2)")
    display(diff_by_cerchia)
    print(f"{metric_title} - differences by month (per km2)")
    display(diff_by_month)

    return {
        "metric": metric_title,
        "most_dangerous_cerchia": str(diff_by_cerchia.index[0]),
        "most_dangerous_month": str(diff_by_month.index[0]),
        "top_cerchia_month_cell": f"{top_cell_cerchia} | {top_cell_month}",
        "top_cell_avg_per_km2": round(top_cell_avg_value, 4),
    }


results = [
    metric_numeric_tables("fatal_incidents_per_km2", "Fatal incidents"),
    metric_numeric_tables("total_incidents_per_km2", "Total incidents"),
    metric_numeric_tables("non_fatal_proxy_per_km2", "Non-fatal proxy (Feriti)"),
]
results_df = pd.DataFrame(results)
print("\\nDanger summary by metric (normalized per km2)")
print("Columns: metric = outcome, most_dangerous_cerchia = ring with highest average per km2,")
print("         most_dangerous_month = month with highest city-average per km2,")
print("         top_cerchia_month_cell = single highest (ring, month) density cell")
display(results_df)
'''


CERCHIE_CELL_2D = '''\
# 2d. Citywide monthly danger using resolved totals
comparison["resolved_total_crashes_per_km2"] = comparison["resolved_total_crashes"] / known_total_area_km2

city_month_danger = (
    comparison.groupby("month", as_index=False)["resolved_total_crashes_per_km2"]
    .mean()
    .sort_values("resolved_total_crashes_per_km2", ascending=False)
    .reset_index(drop=True)
)
city_month_danger["month_label"] = city_month_danger["month"].astype(int).map(month_labels)
city_month_danger["gap_from_most_dangerous_per_km2"] = (
    city_month_danger.loc[0, "resolved_total_crashes_per_km2"]
    - city_month_danger["resolved_total_crashes_per_km2"]
).round(4)

print(
    "Most dangerous month citywide using resolved totals (per km2):",
    city_month_danger.loc[0, "month_label"],
    f"(avg={city_month_danger.loc[0, 'resolved_total_crashes_per_km2']:.4f})",
)
display(
    city_month_danger[
        [
            "month_label",
            "resolved_total_crashes_per_km2",
            "gap_from_most_dangerous_per_km2",
        ]
    ]
)
'''


CERCHIE_CELL_4 = '''\
import matplotlib.pyplot as plt
import pandas as pd

required_vars = [
    "ring_metrics_norm",
    "comparison",
    "month_labels",
    "mismatch_fallbacks",
    "known_total_area_km2",
]
missing_vars = [v for v in required_vars if v not in globals()]
if missing_vars:
    raise ValueError(f"Run the cerchia-tables cells first. Missing variables: {missing_vars}")

month_order = list(range(1, 13))
month_tick_labels = [month_labels[m] for m in month_order]

metric_specs = [
    ("fatal_incidents_per_km2", "Fatal incidents / km2", "#c0392b"),
    ("total_incidents_per_km2", "Total incidents / km2", "#1f77b4"),
    ("non_fatal_proxy_per_km2", "Non-fatal proxy (Feriti) / km2", "#2ca02c"),
]

cerchia_summary = (
    ring_metrics_norm.groupby("Cerchia", as_index=False)[[m[0] for m in metric_specs]]
    .mean()
)

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
for ax, (metric_col, metric_label, color) in zip(axes, metric_specs):
    chart_df = cerchia_summary.sort_values(metric_col, ascending=True)
    ax.barh(chart_df["Cerchia"], chart_df[metric_col], color=color, alpha=0.9)
    ax.set_title(metric_label)
    ax.set_xlabel("Average value per km2")
    ax.grid(axis="x", alpha=0.25)

fig.suptitle("Normalized cerchia comparison", y=1.02, fontsize=14)
plt.tight_layout()
plt.show()

city_month_trend = (
    comparison.groupby("month", as_index=False)["resolved_total_crashes_per_km2"]
    .mean()
    .set_index("month")
    .reindex(month_order)
    .reset_index()
)
city_month_trend["month_label"] = city_month_trend["month"].map(month_labels)

peak_idx = city_month_trend["resolved_total_crashes_per_km2"].idxmax()
low_idx = city_month_trend["resolved_total_crashes_per_km2"].idxmin()

fig, ax = plt.subplots(figsize=(10, 4.8))
ax.plot(
    city_month_trend["month"],
    city_month_trend["resolved_total_crashes_per_km2"],
    marker="o",
    linewidth=2.2,
    color="#34495e",
)
ax.scatter(
    city_month_trend.loc[peak_idx, "month"],
    city_month_trend.loc[peak_idx, "resolved_total_crashes_per_km2"],
    s=90,
    color="#e74c3c",
    zorder=3,
)
ax.scatter(
    city_month_trend.loc[low_idx, "month"],
    city_month_trend.loc[low_idx, "resolved_total_crashes_per_km2"],
    s=90,
    color="#27ae60",
    zorder=3,
)
ax.set_xticks(month_order)
ax.set_xticklabels(month_tick_labels)
ax.set_ylabel("Average resolved total crashes per km2")
ax.set_title("Citywide monthly profile")
ax.grid(alpha=0.25)
plt.tight_layout()
plt.show()

monthly_metric_profiles = (
    ring_metrics_norm.groupby("month", as_index=False)[[m[0] for m in metric_specs]]
    .mean()
    .set_index("month")
    .reindex(month_order)
)

fig, (ax_main, ax_fatal) = plt.subplots(
    2,
    1,
    figsize=(10, 7),
    sharex=True,
    gridspec_kw={"height_ratios": [3.0, 1.8]},
)

for metric_col, metric_label, color in metric_specs:
    if metric_col == "fatal_incidents_per_km2":
        continue
    ax_main.plot(
        month_order,
        monthly_metric_profiles[metric_col],
        marker="o",
        linewidth=2,
        label=metric_label,
        color=color,
    )

fatal_series = monthly_metric_profiles["fatal_incidents_per_km2"]
fatal_range = float(fatal_series.max() - fatal_series.min())
fatal_pad = max(fatal_range * 0.30, 0.005)

ax_fatal.plot(
    month_order,
    fatal_series,
    marker="o",
    linewidth=2.2,
    label="Fatal incidents / km2",
    color="#c0392b",
)
ax_fatal.set_ylim(fatal_series.min() - fatal_pad, fatal_series.max() + fatal_pad)

ax_main.set_ylabel("Average value per km2")
ax_main.set_title("Monthly profiles by normalized metric")
ax_main.grid(alpha=0.25)
ax_main.legend(frameon=False, loc="upper left")

ax_fatal.set_ylabel("Fatal / km2")
ax_fatal.set_xlabel("Month")
ax_fatal.grid(alpha=0.25)
ax_fatal.legend(frameon=False, loc="upper left")
ax_fatal.set_xticks(month_order)
ax_fatal.set_xticklabels(month_tick_labels)

plt.tight_layout()
plt.show()

if not mismatch_fallbacks.empty:
    fallback_plot = mismatch_fallbacks.sort_values(["year", "month"]).copy()
    fallback_plot["year_month"] = (
        fallback_plot["year"].astype(int).astype(str)
        + "-"
        + fallback_plot["month"].astype(int).astype(str).str.zfill(2)
    )
    fallback_plot["fallback_per_km2"] = (
        fallback_plot["fallback_total_from_rings"] / known_total_area_km2
    )

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(
        fallback_plot["year_month"],
        fallback_plot["fallback_per_km2"],
        color="#8e44ad",
        alpha=0.85,
    )
    ax.set_ylabel("Fallback total crashes per km2")
    ax.set_title("Missing monthly totals replaced from city-ring data")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.show()
'''


CERCHIE_CELL_6 = '''\
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import chi2

# Reference ring is Entro la Cerchia dei Navigli so IRRs read as
# "how many times deadlier (or injurier) is ring X vs the core?".
REF_RING = "Entro la Cerchia dei Navigli"

ring_infer = rings.copy()
ring_infer["month_start"] = pd.to_datetime(ring_infer["month_start"], errors="coerce")
ring_infer["month"] = ring_infer["month_start"].dt.month
ring_infer = ring_infer.loc[(ring_infer["Cerchia"] != "Senza indicazioni") & ring_infer["Incidenti"].gt(0)].copy()


severity_rows = []
for cerchia, g in ring_infer.groupby("Cerchia"):
    total_inc = float(g["Incidenti"].sum())
    deaths_rate = 1000 * g["Morti"].sum() / total_inc
    inj_rate = g["Feriti"].sum() / total_inc

    death_ci_low, death_ci_high = bootstrap_rate_ci(g["Morti"], g["Incidenti"], scale=1000, seed=SEED)
    inj_ci_low, inj_ci_high = bootstrap_rate_ci(g["Feriti"], g["Incidenti"], scale=1.0, seed=SEED)

    severity_rows.append(
        {
            "Cerchia": cerchia,
            "Incidenti": int(total_inc),
            "Morti": int(g["Morti"].sum()),
            "Feriti": int(g["Feriti"].sum()),
            "deaths_per_1000_inc": deaths_rate,
            "deaths_ci_low": death_ci_low,
            "deaths_ci_high": death_ci_high,
            "injuries_per_inc": inj_rate,
            "injuries_ci_low": inj_ci_low,
            "injuries_ci_high": inj_ci_high,
        }
    )

severity_infer = pd.DataFrame(severity_rows).sort_values("deaths_per_1000_inc", ascending=False)
print("Severity table with bootstrap 95% CIs (scale: deaths per 1000 crashes, injuries per crash):")
display(severity_infer)

# Poisson rate models with monthly controls, reference ring = REF_RING.
death_formula = f"Morti ~ C(Cerchia, Treatment(reference={REF_RING!r})) + C(month)"
injury_formula = f"Feriti ~ C(Cerchia, Treatment(reference={REF_RING!r})) + C(month)"

death_model = smf.glm(
    formula=death_formula,
    data=ring_infer,
    family=sm.families.Poisson(),
    offset=np.log(ring_infer["Incidenti"]),
).fit(cov_type="HC3")

injury_model = smf.glm(
    formula=injury_formula,
    data=ring_infer,
    family=sm.families.Poisson(),
    offset=np.log(ring_infer["Incidenti"]),
).fit(cov_type="HC3")


def cerchia_irr_table(model, domain: str) -> pd.DataFrame:
    params = model.params
    conf = model.conf_int()
    pvals = model.pvalues
    rows = []
    for term in params.index:
        if "C(Cerchia" not in term:
            continue
        cerchia = term.split("T.", 1)[1].rstrip("]")
        rows.append(
            {
                "domain": domain,
                "cerchia": cerchia,
                "irr_vs_reference": float(np.exp(params[term])),
                "ci_low": float(np.exp(conf.loc[term, 0])),
                "ci_high": float(np.exp(conf.loc[term, 1])),
                "p_value": float(pvals[term]),
            }
        )

    out = pd.DataFrame(rows)
    out["q_value"] = bh_qvalues(out["p_value"])
    out["significant_5pct"] = out["q_value"] < 0.05
    return out.sort_values("q_value")


death_irr = cerchia_irr_table(death_model, "death_rate")
injury_irr = cerchia_irr_table(injury_model, "injury_rate")

print(f"Reference ring (model coding): {REF_RING}")
print("\\nDeath-rate IRR by ring (month-adjusted, HC3 SEs, BH q-values):")
print("Columns: irr_vs_reference = exp(coef), ci_low/high = exp(95% CI), q_value = BH-adjusted p.")
display(death_irr)
print("\\nInjury-rate IRR by ring (month-adjusted, HC3 SEs, BH q-values):")
display(injury_irr)

# Joint Wald test on the ring term — is any ring different from the reference at all?
wald_death = death_model.wald_test_terms(scalar=True)
wald_injury = injury_model.wald_test_terms(scalar=True)
print("\\nJoint Wald test on Cerchia term (scalar = True reports chi2 and df):")
print("Morti:")
print(wald_death)
print("Feriti:")
print(wald_injury)

# Month-seasonality significance by ring.
seasonality_rows = []
for cerchia, g in ring_infer.groupby("Cerchia"):
    month_counts = (
        g.groupby("month", as_index=False)["Incidenti"]
        .sum()
        .set_index("month")
        .reindex(range(1, 13), fill_value=0)["Incidenti"]
        .to_numpy(dtype=float)
    )
    expected = np.repeat(month_counts.sum() / 12, 12)
    chi_stat = float(np.sum((month_counts - expected) ** 2 / expected)) if month_counts.sum() > 0 else np.nan
    p_val = float(1 - chi2.cdf(chi_stat, df=11)) if np.isfinite(chi_stat) else np.nan
    seasonality_rows.append({"Cerchia": cerchia, "chi2_uniform_month": chi_stat, "p_value": p_val})

seasonality_df = pd.DataFrame(seasonality_rows)
seasonality_df["q_value"] = bh_qvalues(seasonality_df["p_value"])
seasonality_df["significant_5pct"] = seasonality_df["q_value"] < 0.05

print("\\nSeasonality test by ring (incidents by month vs uniform profile, df = 11):")
display(seasonality_df.sort_values("q_value"))
'''


def apply_cerchie(nb: dict) -> None:
    cells = _strip_auto_markers(nb["cells"])

    # If the split sub-cells from a prior run are still present, collapse them to
    # a single placeholder so the layout matches the unsplit baseline.
    def _is_split_marker(cell, marker):
        if cell.get("cell_type") != "code":
            return False
        s = cell.get("source", "")
        if isinstance(s, list):
            s = "".join(s)
        return s.lstrip().startswith(marker)

    if (
        len(cells) >= 6
        and _is_split_marker(cells[2], "# 2a.")
        and _is_split_marker(cells[3], "# 2b.")
        and _is_split_marker(cells[4], "# 2c.")
        and _is_split_marker(cells[5], "# 2d.")
    ):
        # Replace the four split cells with a single placeholder so the
        # downstream layout matches the unsplit baseline.
        cells = cells[:2] + [_empty_code_cell("# placeholder — replaced by split cells\n")] + cells[6:]

    # Baseline now: 0 code, 1 md, 2 code, 3 md, 4 code, 5 md, 6 code.

    cells[0] = _empty_code_cell(CERCHIE_CELL_0, metadata=cells[0].get("metadata", {}))

    split_cells = [
        _empty_code_cell(CERCHIE_CELL_2A),
        _empty_code_cell(CERCHIE_CELL_2B),
        _empty_code_cell(CERCHIE_CELL_2C),
        _empty_code_cell(CERCHIE_CELL_2D),
    ]
    cells = cells[:2] + split_cells + cells[3:]

    assert cells[6]["cell_type"] == "markdown"  # "## Visual diagnostics"
    assert cells[7]["cell_type"] == "code"
    cells[7] = _empty_code_cell(CERCHIE_CELL_4, metadata=cells[7].get("metadata", {}))

    assert cells[8]["cell_type"] == "markdown"  # "## Inferential Upgrade"
    assert cells[9]["cell_type"] == "code"
    cells[9] = _empty_code_cell(CERCHIE_CELL_6, metadata=cells[9].get("metadata", {}))

    nb["cells"] = cells


# ---------------------------------------------------------------------------
# CrashDrugUse.ipynb
# ---------------------------------------------------------------------------

CRASHDRUG_CELL_1 = '''\
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

pd.options.display.max_columns = 200
pd.options.display.float_format = "{:.3f}".format

SEED = 42

candidate_roots = [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]
project_root = None
for root in candidate_roots:
    if (root / "data" / "processed").exists():
        project_root = root
        break

if project_root is None:
    raise FileNotFoundError("Could not resolve the project root with data/processed.")

scripts_dir = str(project_root / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from inference_utils import perm_corr, partial_corr_with_year, bh_qvalues  # noqa: E402

processed_dir = project_root / "data" / "processed"
crashes_path = processed_dir / "milan_crashes_monthly_cleaned.csv"
drug_clean_path = processed_dir / "euda_wastewater_ww2026_all_cities_cleaned.csv"

if not crashes_path.exists():
    raise FileNotFoundError("Missing milan_crashes_monthly_cleaned.csv. Run MilanCrashesProcessing.ipynb first.")
if not drug_clean_path.exists():
    raise FileNotFoundError("Missing euda_wastewater_ww2026_all_cities_cleaned.csv. Run DrugUseProcessing.ipynb first.")

crashes = pd.read_csv(crashes_path)
drug_clean = pd.read_csv(drug_clean_path)

print(f"Loaded crashes rows: {len(crashes)}")
print(f"Loaded wastewater cleaned rows: {len(drug_clean)}")
'''


CRASHDRUG_CELL_3 = '''\
# Add Spearman columns alongside the Pearson columns so monotone-but-non-linear
# signals are also detected. Both metrics share the same min-observation rule.
import numpy as np

crash_cols = ["fatal_crashes", "non_fatal_crashes", "total_crashes"]
drug_cols = [c for c in analysis_df.columns if c.startswith("drug_daily_mean_")]


def pairwise_correlations(df: pd.DataFrame, crash_metrics: list[str], drug_metrics: list[str], min_obs: int = 5) -> pd.DataFrame:
    rows = []
    for crash_metric in crash_metrics:
        for drug_metric in drug_metrics:
            pair = df[[crash_metric, drug_metric]].dropna()
            n_obs = int(pair.shape[0])
            if n_obs < min_obs:
                continue
            rows.append(
                {
                    "crash_metric": crash_metric,
                    "drug_metric": drug_metric,
                    "n_obs": n_obs,
                    "pearson_r": pair[crash_metric].corr(pair[drug_metric], method="pearson"),
                    "spearman_rho": pair[crash_metric].corr(pair[drug_metric], method="spearman"),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_pearson_r"] = out["pearson_r"].abs()
    out["abs_spearman_rho"] = out["spearman_rho"].abs()
    return out.sort_values(["abs_pearson_r", "n_obs"], ascending=[False, False]).reset_index(drop=True)


corr_df = pairwise_correlations(analysis_df, crash_cols, drug_cols, min_obs=5)

if corr_df.empty:
    print("No crash-drug pairs have enough shared years for correlation (min_obs=5).")
else:
    print(f"Computed {len(corr_df)} crash-drug correlation pairs.")
    print("Columns: pearson_r = linear level correlation, spearman_rho = rank correlation.")
    display(corr_df.head(20))

    by_crash_summary = (
        corr_df.groupby("crash_metric", as_index=False)
        .agg(
            pairs=("drug_metric", "size"),
            mean_abs_r=("abs_pearson_r", "mean"),
            max_abs_r=("abs_pearson_r", "max"),
            mean_abs_rho=("abs_spearman_rho", "mean"),
            max_abs_rho=("abs_spearman_rho", "max"),
        )
        .sort_values("max_abs_r", ascending=False)
        .reset_index(drop=True)
    )
    display(by_crash_summary)


# Post-hoc power for Pearson r under a Fisher-z approximation. For small n,
# even large true |r| has modest detection power — this calibrates the "no
# robust signal" conclusion.
def pearson_power(n: int, true_r: float, alpha: float = 0.05) -> float:
    if n < 4 or not (-1 < true_r < 1):
        return float("nan")
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha / 2)
    # Fisher z of true r
    z_r = 0.5 * np.log((1 + true_r) / (1 - true_r))
    se = 1.0 / np.sqrt(n - 3)
    crit = z_alpha * se
    return float(norm.sf((crit - z_r) / se) + norm.cdf((-crit - z_r) / se))


power_rows = []
for n in [10, 12, 14]:
    for true_r in [0.3, 0.5, 0.7]:
        power_rows.append(
            {
                "n": n,
                "true_r": true_r,
                "power_alpha_0.05": round(pearson_power(n, true_r), 3),
            }
        )

power_table = pd.DataFrame(power_rows).pivot(index="n", columns="true_r", values="power_alpha_0.05")
power_table.columns = [f"|r|={c}" for c in power_table.columns]
print("\\nPost-hoc power for two-sided Pearson test at alpha=0.05 (Fisher-z approximation):")
display(power_table)
'''


CRASHDRUG_CELL_6 = '''\
# Robustness battery using shared helpers. Reports Pearson raw, year-partial,
# first-difference and one-year-lag tests with BH correction per family.
import numpy as np

rows = []
for crash_metric in crash_cols:
    for drug_metric in drug_cols:
        r_raw, p_raw, n_obs = perm_corr(
            analysis_df[crash_metric], analysis_df[drug_metric], n_perm=8000, seed=SEED,
        )
        r_partial, p_partial, _ = partial_corr_with_year(
            analysis_df[crash_metric],
            analysis_df[drug_metric],
            analysis_df["Year"],
            n_perm=8000,
            seed=SEED,
        )
        r_diff, p_diff, _ = perm_corr(
            analysis_df[crash_metric].diff(), analysis_df[drug_metric].diff(), n_perm=8000, seed=SEED,
        )
        r_lag, p_lag, _ = perm_corr(
            analysis_df[crash_metric].iloc[1:], analysis_df[drug_metric].iloc[:-1], n_perm=8000, seed=SEED,
        )

        rows.append(
            {
                "crash_metric": crash_metric,
                "drug_metric": drug_metric,
                "n_obs": n_obs,
                "r_raw": r_raw,
                "p_raw": p_raw,
                "r_partial": r_partial,
                "p_partial": p_partial,
                "r_diff": r_diff,
                "p_diff": p_diff,
                "r_lag": r_lag,
                "p_lag": p_lag,
            }
        )

robust_df = pd.DataFrame(rows)
robust_df = robust_df.loc[robust_df["n_obs"] >= 5].copy()

robust_df["q_raw"] = bh_qvalues(robust_df["p_raw"])
robust_df["q_partial"] = bh_qvalues(robust_df["p_partial"])
robust_df["q_lag"] = bh_qvalues(robust_df["p_lag"])

robust_df["raw_only_signal"] = (robust_df["q_raw"] < 0.05) & (robust_df["q_partial"] >= 0.05)
robust_df["robust_signal"] = (robust_df["q_partial"] < 0.05) & (robust_df["p_diff"] < 0.05)

print("Top crash-drug pairs by corrected raw significance (BH):")
print("Columns: r_* = correlation, p_* / q_* = permutation p and BH q,")
print("         robust_signal = partial BH-sig AND first-difference p<0.05.")
display(
    robust_df.sort_values("q_raw")[
        [
            "crash_metric",
            "drug_metric",
            "n_obs",
            "r_raw",
            "q_raw",
            "r_partial",
            "q_partial",
            "r_diff",
            "p_diff",
            "r_lag",
            "q_lag",
            "raw_only_signal",
            "robust_signal",
        ]
    ].head(20)
)

summary_counts = pd.Series(
    {
        "eligible_pairs": int(len(robust_df)),
        "raw_significant_q_lt_0_05": int((robust_df["q_raw"] < 0.05).sum()),
        "partial_significant_q_lt_0_05": int((robust_df["q_partial"] < 0.05).sum()),
        "lag_significant_q_lt_0_05": int((robust_df["q_lag"] < 0.05).sum()),
        "robust_signals": int(robust_df["robust_signal"].sum()),
    }
)
print("Robustness counts:")
display(summary_counts.to_frame("value"))

# Leave-one-year-out sign stability for EVERY raw-significant pair (BH q<0.05).
# Previously only the single most significant pair was checked; this version
# reports sign stability system-wide.
sig_raw_pairs = (
    robust_df.loc[robust_df["q_raw"] < 0.05]
    .sort_values("q_raw")
    .reset_index(drop=True)
)

loo_summary_rows = []
loo_series_for_plot = []
for _, row in sig_raw_pairs.iterrows():
    c_metric = row["crash_metric"]
    d_metric = row["drug_metric"]
    full_r = float(row["r_raw"])

    loo_r = []
    for i in range(len(analysis_df)):
        sub = analysis_df.drop(analysis_df.index[i])
        r_loo, _, n_loo = perm_corr(sub[c_metric], sub[d_metric], n_perm=2000, seed=SEED)
        if n_loo >= 5 and np.isfinite(r_loo):
            loo_r.append(r_loo)

    loo_r = np.asarray(loo_r, dtype=float)
    sign_consistency = float((np.sign(loo_r) == np.sign(full_r)).mean()) if len(loo_r) else float("nan")

    loo_summary_rows.append(
        {
            "crash_metric": c_metric,
            "drug_metric": d_metric,
            "full_r": full_r,
            "loo_mean_r": float(np.mean(loo_r)) if len(loo_r) else float("nan"),
            "loo_min_r": float(np.min(loo_r)) if len(loo_r) else float("nan"),
            "loo_max_r": float(np.max(loo_r)) if len(loo_r) else float("nan"),
            "sign_consistency": sign_consistency,
        }
    )
    loo_series_for_plot.append((c_metric, d_metric, full_r, loo_r))

if loo_summary_rows:
    print("\\nLeave-one-year-out sign stability for every raw BH-significant pair:")
    print("Columns: sign_consistency = share of LOO fits whose r sign matches the full sample.")
    display(pd.DataFrame(loo_summary_rows))

    n_plots = len(loo_series_for_plot)
    fig, axes = plt.subplots(1, n_plots, figsize=(4.5 * n_plots, 4.0), squeeze=False)
    for ax, (c_metric, d_metric, full_r, loo_r) in zip(axes[0], loo_series_for_plot):
        ax.hist(loo_r, bins=10, color="#4c78a8", alpha=0.85)
        ax.axvline(full_r, color="#d62728", linestyle="--", linewidth=2, label="full-sample r")
        ax.set_title(f"{c_metric}\\n vs {d_metric.replace('drug_daily_mean_', '')}", fontsize=9)
        ax.set_xlabel("LOO Pearson r")
        ax.set_ylabel("Frequency")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    plt.tight_layout()
    plt.show()
else:
    print("\\nNo raw BH-significant pairs to run LOO on.")
'''


def apply_crashdrug(nb: dict) -> None:
    cells = _strip_auto_markers(nb["cells"])
    # Original: 0 md, 1 code, 2 code, 3 code, 4 code, 5 md, 6 code.
    assert cells[1]["cell_type"] == "code"
    cells[1] = _empty_code_cell(CRASHDRUG_CELL_1, metadata=cells[1].get("metadata", {}))

    assert cells[3]["cell_type"] == "code"
    cells[3] = _empty_code_cell(CRASHDRUG_CELL_3, metadata=cells[3].get("metadata", {}))

    assert cells[6]["cell_type"] == "code"
    cells[6] = _empty_code_cell(CRASHDRUG_CELL_6, metadata=cells[6].get("metadata", {}))

    nb["cells"] = cells


# ---------------------------------------------------------------------------
# Fleet.ipynb
# ---------------------------------------------------------------------------

FLEET_CELL_1 = '''\
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.options.display.max_columns = 200
pd.options.display.float_format = "{:.4f}".format

SEED = 42

candidate_roots = [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]
project_root = None
for root in candidate_roots:
    if (root / "data" / "processed").exists():
        project_root = root
        break

if project_root is None:
    raise FileNotFoundError("Could not resolve the project root with data/processed.")

scripts_dir = str(project_root / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from inference_utils import (  # noqa: E402
    perm_corr,
    partial_corr_with_year,
    residualize_linear,
    slope_perm_test,
    bootstrap_slope_ci,
    bh_qvalues,
)

processed_dir = project_root / "data" / "processed"
fleet_path = processed_dir / "milan_vehicle_fleet_cleaned.csv"
crashes_path = processed_dir / "milan_crashes_monthly_cleaned.csv"

if not fleet_path.exists():
    raise FileNotFoundError("Missing milan_vehicle_fleet_cleaned.csv. Run VehiclesProcessing.ipynb first.")
if not crashes_path.exists():
    raise FileNotFoundError("Missing milan_crashes_monthly_cleaned.csv. Run MilanCrashesProcessing.ipynb first.")

fleet = pd.read_csv(fleet_path)
crashes_monthly = pd.read_csv(crashes_path)

print(f"Project root: {project_root}")
print(f"Fleet rows: {len(fleet)}")
print(f"Crash-month rows: {len(crashes_monthly)}")
'''


FLEET_CELL_4 = '''\
# Raw Pearson + Spearman with permutation p-values, using the shared helper.

fleet_metrics = ["fleet_total", "fleet_cars", "fleet_motorcycles", "fleet_heavy_goods", "car_share", "motorcycle_share"]
crash_metrics = [
    "total_crashes",
    "fatal_crashes",
    "deaths",
    "injuries",
    "crashes_per_10k_fleet",
    "fatal_crashes_per_100k_fleet",
    "deaths_per_100k_fleet",
]

rows = []
for crash_metric in crash_metrics:
    for fleet_metric in fleet_metrics:
        pearson_r, pearson_p, n_obs = perm_corr(
            analysis_df[fleet_metric], analysis_df[crash_metric], method="pearson", n_perm=12000, seed=SEED,
        )
        spearman_r, spearman_p, _ = perm_corr(
            analysis_df[fleet_metric], analysis_df[crash_metric], method="spearman", n_perm=12000, seed=SEED,
        )
        rows.append(
            {
                "crash_metric": crash_metric,
                "fleet_metric": fleet_metric,
                "n_obs": n_obs,
                "pearson_r": pearson_r,
                "pearson_p_perm": pearson_p,
                "spearman_rho": spearman_r,
                "spearman_p_perm": spearman_p,
            }
        )

raw_corr = pd.DataFrame(rows)
raw_corr["abs_pearson_r"] = raw_corr["pearson_r"].abs()
raw_corr = raw_corr.sort_values(["pearson_p_perm", "abs_pearson_r"], ascending=[True, False]).reset_index(drop=True)

print("Top raw correlations (permutation p-values):")
print("Columns: pearson_r / spearman_rho = observed correlation, *_p_perm = permutation p-value.")
display(raw_corr.head(20))

sig_raw = raw_corr.loc[raw_corr["pearson_p_perm"] < 0.05].copy()
print(f"Significant raw Pearson pairs (p < 0.05): {len(sig_raw)}")
display(sig_raw.head(20))
'''


FLEET_CELL_5 = '''\
# Trend-adjusted partial correlations and first-difference tests via shared helpers.

rows_partial = []
for crash_metric in ["total_crashes", "fatal_crashes", "deaths", "injuries"]:
    for fleet_metric in fleet_metrics:
        sub = analysis_df[["Year", fleet_metric, crash_metric]].dropna()
        r_partial, p_partial, n_obs = partial_corr_with_year(
            sub[fleet_metric], sub[crash_metric], sub["Year"], method="pearson", n_perm=12000, seed=SEED,
        )
        rows_partial.append(
            {
                "fleet_metric": fleet_metric,
                "crash_metric": crash_metric,
                "n_obs": n_obs,
                "partial_r": r_partial,
                "partial_p_perm": p_partial,
            }
        )

partial_corr = pd.DataFrame(rows_partial)
partial_corr["abs_partial_r"] = partial_corr["partial_r"].abs()
partial_corr = partial_corr.sort_values(["partial_p_perm", "abs_partial_r"], ascending=[True, False]).reset_index(drop=True)

print("Top trend-adjusted partial correlations (controlling for year):")
display(partial_corr.head(20))

# First-difference analysis (annualized to handle year gaps).
diff_metrics = fleet_metrics + ["total_crashes", "fatal_crashes", "deaths", "injuries"]
diff_df = analysis_df[["Year"] + diff_metrics].copy()
diff_df["year_gap"] = diff_df["Year"].diff()
for col in diff_metrics:
    diff_df[f"d_{col}"] = diff_df[col].diff() / diff_df["year_gap"]

diff_df = diff_df.dropna().reset_index(drop=True)

rows_diff = []
for crash_metric in ["d_total_crashes", "d_fatal_crashes", "d_deaths", "d_injuries"]:
    for fleet_metric in [f"d_{m}" for m in fleet_metrics]:
        r, p, n_obs = perm_corr(
            diff_df[fleet_metric], diff_df[crash_metric], method="pearson", n_perm=12000, seed=SEED,
        )
        rows_diff.append(
            {
                "crash_metric": crash_metric,
                "fleet_metric": fleet_metric,
                "n_obs": n_obs,
                "pearson_r": r,
                "pearson_p_perm": p,
            }
        )

diff_corr = pd.DataFrame(rows_diff)
diff_corr["abs_pearson_r"] = diff_corr["pearson_r"].abs()
diff_corr = diff_corr.sort_values(["pearson_p_perm", "abs_pearson_r"], ascending=[True, False]).reset_index(drop=True)

print(f"First-difference sample size: {len(diff_df)} yearly changes")
print("Top first-difference correlations:")
display(diff_corr.head(20))
'''


FLEET_CELL_6 = '''\
# Sensitivity: trend-adjusted partial correlation for total_crashes on different periods.

periods = {
    "full_2004_2022": analysis_df,
    "pre_covid_2004_2019": analysis_df.loc[analysis_df["Year"] <= 2019],
    "post_2010_2010_2022": analysis_df.loc[analysis_df["Year"] >= 2010],
}

sensitivity_rows = []
for period_name, frame in periods.items():
    for fleet_metric in ["fleet_total", "fleet_heavy_goods", "motorcycle_share", "fleet_cars"]:
        sub = frame[["Year", fleet_metric, "total_crashes"]].dropna()
        r, p, n_obs = partial_corr_with_year(
            sub[fleet_metric], sub["total_crashes"], sub["Year"], method="pearson", n_perm=8000, seed=SEED,
        )
        sensitivity_rows.append(
            {
                "period": period_name,
                "fleet_metric": fleet_metric,
                "n_obs": n_obs,
                "partial_r": r,
                "partial_p_perm": p,
            }
        )

sensitivity_df = pd.DataFrame(sensitivity_rows).sort_values(["fleet_metric", "period"]).reset_index(drop=True)
print("Sensitivity check: year-controlled partial correlations for total_crashes")
print("A stable relationship should keep the same sign and rough magnitude across all three windows.")
display(sensitivity_df)
'''


FLEET_CELL_7 = '''\
# Exposure-adjusted long-run trend tests using the shared slope + bootstrap helpers.

trend_targets = [
    "total_crashes",
    "crashes_per_10k_fleet",
    "fatal_crashes_per_100k_fleet",
    "deaths_per_100k_fleet",
]

trend_rows = []
for metric in trend_targets:
    slope, p_val = slope_perm_test(analysis_df["Year"], analysis_df[metric], n_perm=15000, seed=SEED)
    ci_low, ci_high = bootstrap_slope_ci(analysis_df["Year"], analysis_df[metric], n_boot=5000, seed=SEED)
    trend_rows.append(
        {
            "metric": metric,
            "slope_per_year": slope,
            "perm_p_value": p_val,
            "slope_ci_low": ci_low,
            "slope_ci_high": ci_high,
        }
    )

trend_stats = pd.DataFrame(trend_rows).sort_values("perm_p_value").reset_index(drop=True)
print("Exposure-adjusted long-run trends (slope per year, permutation p, bootstrap 95% CI):")
display(trend_stats)

years = analysis_df["Year"].astype(int).tolist()
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharex=True)

for ax, metric, color in [
    (axes[0], "crashes_per_10k_fleet", "#1d3557"),
    (axes[1], "fatal_crashes_per_100k_fleet", "#e63946"),
]:
    x = analysis_df["Year"].to_numpy(dtype=float)
    y = analysis_df[metric].to_numpy(dtype=float)
    slope = np.sum((x - x.mean()) * (y - y.mean())) / np.sum((x - x.mean()) ** 2)
    intercept = y.mean() - slope * x.mean()

    ax.plot(analysis_df["Year"], y, marker="o", linewidth=2, color=color, label=metric)
    ax.plot(analysis_df["Year"], intercept + slope * x, linestyle="--", color="#444444", label="linear trend")
    ax.set_title(metric)
    ax.set_xlabel("Year")
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha="right")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)

axes[0].set_ylabel("Rate")
plt.tight_layout()
plt.show()
'''


FLEET_CELL_8 = '''\
# Tidy summary table — replaces the prior inline print-format snippet.

alpha = 0.05

raw_total = raw_corr.loc[raw_corr["crash_metric"] == "total_crashes"].sort_values("pearson_p_perm")
partial_total = partial_corr.loc[partial_corr["crash_metric"] == "total_crashes"].sort_values("partial_p_perm")
diff_sig_count = int((diff_corr["pearson_p_perm"] < alpha).sum())
trend_sig = trend_stats.loc[trend_stats["perm_p_value"] < alpha].copy()

summary_rows = []
for fleet_var in ["fleet_cars", "fleet_motorcycles", "fleet_total", "fleet_heavy_goods", "motorcycle_share"]:
    raw_slice = raw_total.loc[raw_total["fleet_metric"] == fleet_var]
    partial_slice = partial_total.loc[partial_total["fleet_metric"] == fleet_var]
    if raw_slice.empty or partial_slice.empty:
        continue
    summary_rows.append(
        {
            "fleet_var": fleet_var,
            "raw_r": float(raw_slice["pearson_r"].iloc[0]),
            "raw_p_perm": float(raw_slice["pearson_p_perm"].iloc[0]),
            "partial_r": float(partial_slice["partial_r"].iloc[0]),
            "partial_p_perm": float(partial_slice["partial_p_perm"].iloc[0]),
        }
    )

total_summary = pd.DataFrame(summary_rows)
print("Per-fleet summary for total_crashes (raw vs trend-adjusted):")
display(total_summary)

print(f"First-difference pairs with p<{alpha}: {diff_sig_count}")

print("\\nExposure-adjusted trend summary (significant at alpha=0.05):")
display(trend_sig)

print("\\nSensitivity by period (year-controlled partial for total_crashes):")
display(sensitivity_df.loc[sensitivity_df["fleet_metric"].isin(["fleet_total", "fleet_heavy_goods", "motorcycle_share"])].sort_values(["fleet_metric", "period"]).reset_index(drop=True))
'''


FLEET_CELL_11 = '''\
# BH correction across test families + regime-shift diagnostics with bootstrap CI.
# Regime tests are now run for motorcycle_share, car_share, and heavy_goods_share
# so the asymmetry across composition variables is visible.
import statsmodels.formula.api as smf

raw_corr_adj = raw_corr.copy()
raw_corr_adj["q_pearson_bh"] = bh_qvalues(raw_corr_adj["pearson_p_perm"])
raw_corr_adj["raw_significant_5pct"] = raw_corr_adj["q_pearson_bh"] < 0.05

partial_corr_adj = partial_corr.copy()
partial_corr_adj["q_partial_bh"] = bh_qvalues(partial_corr_adj["partial_p_perm"])
partial_corr_adj["partial_significant_5pct"] = partial_corr_adj["q_partial_bh"] < 0.05

diff_corr_adj = diff_corr.copy()
diff_corr_adj["q_diff_bh"] = bh_qvalues(diff_corr_adj["pearson_p_perm"])
diff_corr_adj["diff_significant_5pct"] = diff_corr_adj["q_diff_bh"] < 0.05

robust_pairs = (
    partial_corr_adj.merge(
        raw_corr_adj[["crash_metric", "fleet_metric", "pearson_r", "q_pearson_bh"]],
        on=["crash_metric", "fleet_metric"],
        how="left",
    )
    .assign(
        sign_stable=lambda d: np.sign(d["partial_r"]) == np.sign(d["pearson_r"]),
        robust_evidence=lambda d: (d["q_partial_bh"] < 0.05) & (np.sign(d["partial_r"]) == np.sign(d["pearson_r"])),
    )
    .sort_values("q_partial_bh")
)

print("Top trend-adjusted pairs with BH correction:")
print("Columns: pearson_r = raw, partial_r = year-controlled, q_* = BH q,")
print("         robust_evidence = BH-sig partial AND sign agrees with raw.")
display(
    robust_pairs[
        [
            "crash_metric",
            "fleet_metric",
            "pearson_r",
            "q_pearson_bh",
            "partial_r",
            "q_partial_bh",
            "sign_stable",
            "robust_evidence",
        ]
    ].head(20)
)

count_summary = pd.Series(
    {
        "raw_significant_q_lt_0_05": int(raw_corr_adj["raw_significant_5pct"].sum()),
        "partial_significant_q_lt_0_05": int(partial_corr_adj["partial_significant_5pct"].sum()),
        "first_diff_significant_q_lt_0_05": int(diff_corr_adj["diff_significant_5pct"].sum()),
        "robust_evidence_pairs": int(robust_pairs["robust_evidence"].sum()),
    }
)
print("Corrected significance counts:")
display(count_summary.to_frame("value"))

# Regime-shift interaction for multiple composition variables.
regime_df = analysis_df.copy()
regime_df["post2020"] = (regime_df["Year"] >= 2020).astype(int)

regime_vars = ["motorcycle_share", "car_share"]
if "heavy_goods_share" not in regime_df.columns:
    regime_df["heavy_goods_share"] = regime_df["fleet_heavy_goods"] / regime_df["fleet_total"]
regime_vars.append("heavy_goods_share")

regime_rows = []
rng = np.random.default_rng(SEED)
for var in regime_vars:
    formula = f"total_crashes ~ Year + {var} + post2020 + {var}:post2020"
    model = smf.ols(formula, data=regime_df).fit(cov_type="HC3")
    interaction_term = f"{var}:post2020"
    coef = float(model.params[interaction_term])
    se = float(model.bse[interaction_term])
    pval = float(model.pvalues[interaction_term])

    # Case-resampling bootstrap CI (pairs bootstrap) — wild bootstrap alternative
    # would also be fine but pairs is simpler and handles HC3-style heteroscedasticity.
    boot_coefs = []
    n = len(regime_df)
    for _ in range(4000):
        idx = rng.integers(0, n, n)
        sample = regime_df.iloc[idx]
        try:
            m_b = smf.ols(formula, data=sample).fit()
            boot_coefs.append(float(m_b.params[interaction_term]))
        except Exception:
            continue
    if boot_coefs:
        ci_low, ci_high = (
            float(np.quantile(boot_coefs, 0.025)),
            float(np.quantile(boot_coefs, 0.975)),
        )
    else:
        ci_low = ci_high = float("nan")

    regime_rows.append(
        {
            "composition_var": var,
            "coef": coef,
            "hc3_std_err": se,
            "p_value_hc3": pval,
            "boot_ci_low": ci_low,
            "boot_ci_high": ci_high,
        }
    )

regime_table = pd.DataFrame(regime_rows)
regime_table["q_value_bh"] = bh_qvalues(regime_table["p_value_hc3"])
print("\\nRegime-shift interaction tests (total_crashes ~ Year + X + post2020 + X:post2020):")
print("Columns: coef = interaction estimate, boot_ci_* = pairs-bootstrap 95% CI (4000 draws).")
display(regime_table)

# Rolling-window correlations for a grid of composition variables and crash outcomes.
# Materialize heavy_goods_share on analysis_df so the rolling helper can read it.
if "heavy_goods_share" not in analysis_df.columns:
    analysis_df = analysis_df.assign(heavy_goods_share=analysis_df["fleet_heavy_goods"] / analysis_df["fleet_total"])

window = 8
pair_grid = [
    ("motorcycle_share", "total_crashes"),
    ("motorcycle_share", "fatal_crashes"),
    ("car_share", "total_crashes"),
    ("heavy_goods_share", "total_crashes"),
]

roll_rows = []
for fleet_v, crash_v in pair_grid:
    for i in range(0, len(analysis_df) - window + 1):
        sub = analysis_df.iloc[i : i + window]
        if sub[fleet_v].nunique() < 2 or sub[crash_v].nunique() < 2:
            continue
        roll_rows.append(
            {
                "fleet_var": fleet_v,
                "crash_var": crash_v,
                "end_year": int(sub["Year"].iloc[-1]),
                "correlation": float(np.corrcoef(sub[fleet_v], sub[crash_v])[0, 1]),
            }
        )
rolling_corr_grid = pd.DataFrame(roll_rows)

fig, ax = plt.subplots(figsize=(10.5, 5.5))
palette = {
    ("motorcycle_share", "total_crashes"): "#2a9d8f",
    ("motorcycle_share", "fatal_crashes"): "#e76f51",
    ("car_share", "total_crashes"): "#1d3557",
    ("heavy_goods_share", "total_crashes"): "#8e44ad",
}
for (fv, cv), color in palette.items():
    sub = rolling_corr_grid.loc[(rolling_corr_grid["fleet_var"] == fv) & (rolling_corr_grid["crash_var"] == cv)]
    if sub.empty:
        continue
    ax.plot(sub["end_year"], sub["correlation"], marker="o", linewidth=2, label=f"{fv} vs {cv}", color=color)

ax.axhline(0, color="#666666", linewidth=1)
ax.set_title(f"{window}-year rolling correlations")
ax.set_xlabel("Window end year")
ax.set_ylabel("Correlation")
ax.legend(frameon=False, loc="best")
ax.grid(alpha=0.25)
plt.tight_layout()
plt.show()

print("Rolling-window correlation table (long format):")
display(rolling_corr_grid.head(40))
'''


def apply_fleet(nb: dict) -> None:
    cells = _strip_auto_markers(nb["cells"])
    # Original: 0 md, 1 code, 2 code, 3 code, 4 code, 5 code, 6 code, 7 code, 8 code, 9 md, 10 md, 11 code.

    assert cells[1]["cell_type"] == "code"
    cells[1] = _empty_code_cell(FLEET_CELL_1, metadata=cells[1].get("metadata", {}))

    # Cells 2 (aggregation) and 3 (trend plot) keep their original source but we can leave them.

    # Cell 4: raw correlations
    assert cells[4]["cell_type"] == "code"
    cells[4] = _empty_code_cell(FLEET_CELL_4, metadata=cells[4].get("metadata", {}))

    # Cell 5: partial + first-difference
    assert cells[5]["cell_type"] == "code"
    cells[5] = _empty_code_cell(FLEET_CELL_5, metadata=cells[5].get("metadata", {}))

    # Cell 6: period sensitivity
    assert cells[6]["cell_type"] == "code"
    cells[6] = _empty_code_cell(FLEET_CELL_6, metadata=cells[6].get("metadata", {}))

    # Cell 7: slope test
    assert cells[7]["cell_type"] == "code"
    cells[7] = _empty_code_cell(FLEET_CELL_7, metadata=cells[7].get("metadata", {}))

    # Cell 8: tidy summary
    assert cells[8]["cell_type"] == "code"
    cells[8] = _empty_code_cell(FLEET_CELL_8, metadata=cells[8].get("metadata", {}))

    # Cell 11: BH + regime + rolling
    assert cells[11]["cell_type"] == "code"
    cells[11] = _empty_code_cell(FLEET_CELL_11, metadata=cells[11].get("metadata", {}))

    nb["cells"] = cells


# ---------------------------------------------------------------------------
# CrashType.ipynb
# ---------------------------------------------------------------------------

CRASHTYPE_CELL_1 = '''\
from pathlib import Path
from itertools import combinations
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats
from scipy.linalg import lstsq
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
import statsmodels.formula.api as smf

from sklearn.model_selection import StratifiedKFold, TimeSeriesSplit, cross_val_score, train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

sns.set_theme(style="whitegrid", context="notebook")

SEED = 42
np.random.seed(SEED)
pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 140)

candidate_roots = [Path.cwd(), Path.cwd().parent, Path.cwd().parent.parent]
for root in candidate_roots:
    if (root / "scripts").exists():
        sys.path.insert(0, str(root / "scripts"))
        break

from inference_utils import (  # noqa: E402
    perm_corr,
    partial_corr_with_year,
    residualize_with_controls,
    bootstrap_corr_ci,
    cramers_v,
    bh_qvalues,
)
'''


CRASHTYPE_CELL_9 = '''\
type_totals = (
    analysis_df.groupby("crash_type", as_index=False)
    .agg(total_incidents=("Incidenti", "sum"),
         mean_share=("type_share", "mean"),
         mean_fatal_rate_1000=("fatal_rate_1000", "mean"),
         mean_injury_rate=("injury_rate", "mean"))
    .sort_values("total_incidents", ascending=False)
)
display(type_totals)

fig, axes = plt.subplots(2, 2, figsize=(16, 11))

sns.barplot(
    data=type_totals,
    x="total_incidents",
    y="crash_type",
    hue="crash_type",
    legend=False,
    ax=axes[0, 0],
    palette="Blues_r",
)
axes[0, 0].set_title("Total incidents by crash type")
axes[0, 0].set_xlabel("Total incidents")
axes[0, 0].set_ylabel("Crash type")

sns.boxplot(data=analysis_df, x="crash_type", y="type_share", ax=axes[0, 1], color="#7cb342")
axes[0, 1].set_title("Monthly share distribution by crash type")
axes[0, 1].tick_params(axis="x", rotation=70)

sns.violinplot(data=analysis_df, x="crash_type", y="fatal_rate_1000", ax=axes[1, 0], color="#ef6c00", inner="quartile")
axes[1, 0].set_title("Fatality rate per 1000 incidents")
axes[1, 0].tick_params(axis="x", rotation=70)

heat_df = (
    analysis_df.groupby("crash_type")[["type_share", "fatal_rate_1000", "injury_rate", "share_1v", "share_2v", "share_3plus", "zone_hhi"]]
    .mean()
)
sns.heatmap(heat_df, cmap="YlGnBu", annot=True, fmt=".2f", ax=axes[1, 1])
axes[1, 1].set_title("Average context metrics by crash type")

plt.tight_layout()
plt.show()

# Stratified pairplot sample so minority classes are not underrepresented.
pair_cols = ["type_share", "fatal_rate_1000", "injury_rate", "share_1v", "share_2v", "share_3plus", "crash_type"]
pair_base = analysis_df[pair_cols].dropna()
per_class_cap = 80
pair_sample = pd.concat(
    [
        g.sample(min(len(g), per_class_cap), random_state=SEED)
        for _, g in pair_base.groupby("crash_type")
    ]
)
sns.pairplot(
    pair_sample,
    vars=["type_share", "fatal_rate_1000", "injury_rate", "share_1v", "share_2v", "share_3plus"],
    hue="crash_type",
    corner=True,
    plot_kws={"alpha": 0.4, "s": 12},
)
plt.show()
'''


CRASHTYPE_CELL_13 = '''\
# Drop share_3plus at the model level too: the three vehicle shares sum to 1
# so one must be omitted to avoid a near-singular design matrix in every
# downstream regression.
model_cols_num = [
    "IncidentiTotali",
    "IncidentiMortali",
    "FeritiTotaliMese",
    "MortiTotaliMese",
    "share_1v",
    "share_2v",
    "zone_hhi",
    "month",
    "year",
]
model_cols_cat = ["season", "multi_vehicle_regime", "location_cluster", "severity_level"]

model_df = analysis_df[["crash_type", "month_start", *model_cols_num, *model_cols_cat]].copy()
model_df = model_df.dropna(subset=["crash_type"])

X = model_df[model_cols_num + model_cols_cat]
y = model_df["crash_type"]

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, model_cols_num),
        ("cat", categorical_transformer, model_cols_cat),
    ]
)

logit_model = Pipeline(steps=[
    ("prep", preprocessor),
    ("clf", LogisticRegression(max_iter=5000, class_weight="balanced")),
])

rf_model = Pipeline(steps=[
    ("prep", preprocessor),
    ("clf", RandomForestClassifier(n_estimators=500, min_samples_leaf=3, random_state=SEED, class_weight="balanced_subsample")),
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
logit_f1 = cross_val_score(logit_model, X, y, cv=cv, scoring="f1_macro")
rf_f1 = cross_val_score(rf_model, X, y, cv=cv, scoring="f1_macro")
logit_acc = cross_val_score(logit_model, X, y, cv=cv, scoring="accuracy")
rf_acc = cross_val_score(rf_model, X, y, cv=cv, scoring="accuracy")

cv_summary = pd.DataFrame(
    {
        "model": ["multinomial_logit", "random_forest"],
        "macro_f1_mean": [logit_f1.mean(), rf_f1.mean()],
        "macro_f1_std": [logit_f1.std(), rf_f1.std()],
        "accuracy_mean": [logit_acc.mean(), rf_acc.mean()],
        "accuracy_std": [logit_acc.std(), rf_acc.std()],
    }
)

print("Cross-validated model performance (stratified random k-fold — see temporal holdout below for the honest read):")
display(cv_summary)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=SEED, stratify=y)

best_model_name = "multinomial_logit" if logit_f1.mean() >= rf_f1.mean() else "random_forest"
best_model = logit_model if best_model_name == "multinomial_logit" else rf_model
best_model.fit(X_train, y_train)
y_pred = best_model.predict(X_test)

print(f"Selected model based on macro-F1: {best_model_name}")
print("\\nClassification report on holdout set:")
print(classification_report(y_test, y_pred, zero_division=0))

fig, ax = plt.subplots(figsize=(10, 8))
ConfusionMatrixDisplay.from_predictions(y_test, y_pred, xticks_rotation=75, cmap="Blues", ax=ax)
ax.set_title(f"Confusion matrix ({best_model_name})")
plt.show()

logit_model.fit(X, y)
feat_names = logit_model.named_steps["prep"].get_feature_names_out()
coef = logit_model.named_steps["clf"].coef_
classes = logit_model.named_steps["clf"].classes_

coef_rows = []
for i, cls in enumerate(classes):
    top_idx = np.argsort(np.abs(coef[i]))[::-1][:8]
    for j in top_idx:
        coef_rows.append({
            "crash_type": cls,
            "feature": feat_names[j],
            "coef": coef[i, j],
            "odds_ratio": np.exp(coef[i, j]),
        })

logit_effects = pd.DataFrame(coef_rows)
print("Top multinomial-logit effects by absolute coefficient:")
print("Columns: feature = engineered predictor, odds_ratio = exp(coef) — multiplicative effect on relative odds.")
display(logit_effects)
'''


CRASHTYPE_CELL_19 = '''\
# Severity GLMs now control for month and a linear year trend so crash-type
# IRRs describe per-crash severity net of era and seasonality confounding.
rate_df = nature_clean[nature_clean["Incidenti"] > 0].copy()
rate_df["year"] = rate_df["month_start"].dt.year
rate_df["month"] = rate_df["month_start"].dt.month

severity_formula = "{outcome} ~ C(crash_type) + C(month) + year"

death_glm = smf.glm(
    formula=severity_formula.format(outcome="Morti"),
    data=rate_df,
    family=sm.families.Poisson(),
    offset=np.log(rate_df["Incidenti"]),
).fit(cov_type="HC3")

injury_glm = smf.glm(
    formula=severity_formula.format(outcome="Feriti"),
    data=rate_df,
    family=sm.families.Poisson(),
    offset=np.log(rate_df["Incidenti"]),
).fit(cov_type="HC3")


def glm_to_irr_table(model, outcome_name: str) -> pd.DataFrame:
    params = model.params
    conf = model.conf_int()
    pvals = model.pvalues

    rows = []
    for term in params.index:
        if "C(crash_type)" not in term:
            continue
        t_name = term.split("T.", 1)[1].rstrip("]")
        rows.append(
            {
                "domain": f"{outcome_name}_rate_vs_reference",
                "crash_type": t_name,
                "metric": outcome_name,
                "estimate": float(np.exp(params[term])),
                "ci_low": float(np.exp(conf.loc[term, 0])),
                "ci_high": float(np.exp(conf.loc[term, 1])),
                "p_value": float(pvals[term]),
            }
        )

    out = pd.DataFrame(rows)
    out["q_value"] = bh_qvalues(out["p_value"])
    out["direction"] = np.where(out["estimate"] > 1, "higher_than_reference", "lower_than_reference")
    out["supported"] = out["q_value"] < 0.05
    return out.sort_values("q_value")


death_irr = glm_to_irr_table(death_glm, "death")
injury_irr = glm_to_irr_table(injury_glm, "injury")

corr_findings = robust_corr.copy()
corr_findings = corr_findings.assign(
    domain="partial_spearman",
    estimate=corr_findings["rho_partial"],
    q_value=corr_findings["q_partial"],
    direction=np.where(corr_findings["rho_partial"] > 0, "positive", "negative"),
    supported=True,
)
corr_findings = corr_findings[["domain", "crash_type", "metric", "estimate", "ci_low", "ci_high", "q_value", "direction", "supported"]]

rate_findings = pd.concat([death_irr, injury_irr], ignore_index=True)
rate_findings = rate_findings[["domain", "crash_type", "metric", "estimate", "ci_low", "ci_high", "q_value", "direction", "supported"]]

findings_table = pd.concat([corr_findings, rate_findings], ignore_index=True)
findings_table = findings_table.sort_values(["supported", "q_value"], ascending=[False, True])

print("Reference class used by GLM coding:", sorted(rate_df["crash_type"].unique())[0])
print("Severity GLMs include C(month) and year to remove seasonal and era confounding.")
print("\\nStatistically supported findings (q < 0.05):")
display(findings_table[findings_table["supported"]].head(60))

summary_points = []

if not robust_corr.empty:
    top_corr = robust_corr.iloc[0]
    summary_points.append(
        f"Strongest robust correlation: {top_corr['crash_type']} with {top_corr['metric']} (partial rho={top_corr['rho_partial']:.3f}, q={top_corr['q_partial']:.2e})."
    )

sig_death = death_irr[death_irr["supported"]].sort_values("estimate", ascending=False)
if not sig_death.empty:
    top_death = sig_death.iloc[0]
    summary_points.append(
        f"Highest adjusted death rate vs reference (month+year controlled): {top_death['crash_type']} (IRR={top_death['estimate']:.2f}, 95% CI [{top_death['ci_low']:.2f}, {top_death['ci_high']:.2f}], q={top_death['q_value']:.2e})."
    )

sig_injury = injury_irr[injury_irr["supported"]].sort_values("estimate", ascending=False)
if not sig_injury.empty:
    top_injury = sig_injury.iloc[0]
    summary_points.append(
        f"Highest adjusted injury rate vs reference (month+year controlled): {top_injury['crash_type']} (IRR={top_injury['estimate']:.2f}, 95% CI [{top_injury['ci_low']:.2f}, {top_injury['ci_high']:.2f}], q={top_injury['q_value']:.2e})."
    )

print("\\nConcise conclusions:")
for i, line in enumerate(summary_points, start=1):
    print(f"{i}. {line}")
'''


def apply_crashtype(nb: dict) -> None:
    cells = _strip_auto_markers(nb["cells"])
    # Original layout indices (code cells): 1 imports, 3 load, 5 clean, 7 engineer,
    # 9 EDA plots, 11 tests, 13 models, 15 iter, 17 correlations, 19 IRRs, 21 temporal.

    assert cells[1]["cell_type"] == "code"
    cells[1] = _empty_code_cell(CRASHTYPE_CELL_1, metadata=cells[1].get("metadata", {}))

    assert cells[9]["cell_type"] == "code"
    cells[9] = _empty_code_cell(CRASHTYPE_CELL_9, metadata=cells[9].get("metadata", {}))

    assert cells[13]["cell_type"] == "code"
    cells[13] = _empty_code_cell(CRASHTYPE_CELL_13, metadata=cells[13].get("metadata", {}))

    assert cells[19]["cell_type"] == "code"
    cells[19] = _empty_code_cell(CRASHTYPE_CELL_19, metadata=cells[19].get("metadata", {}))

    nb["cells"] = cells


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cases = [
        ("Cerchie.ipynb", apply_cerchie),
        ("CrashDrugUse.ipynb", apply_crashdrug),
        ("Fleet.ipynb", apply_fleet),
        ("CrashType.ipynb", apply_crashtype),
    ]
    for name, fn in cases:
        nb = load(name)
        fn(nb)
        save(name, nb)
        print(f"updated {name}: now {len(nb['cells'])} cells (explainer markdown stripped)")


if __name__ == "__main__":
    main()
