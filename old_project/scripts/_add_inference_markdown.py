"""One-off utility: insert explanatory markdown cells after each code cell
in the four inference notebooks.

Idempotent: a marker string in the frontmatter of each inserted markdown cell
identifies it, so re-running the script replaces old inserts in place instead
of stacking duplicates.
"""
from __future__ import annotations

import json
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INFERENCE = ROOT / "notebooks" / "inference"

MARKER = "<!-- auto-explainer:v1 -->"


def md_cell(body: str) -> dict:
    source = f"{MARKER}\n\n{body.strip()}\n"
    return {
        "cell_type": "markdown",
        "metadata": {"tags": ["auto-explainer"]},
        "source": source.splitlines(keepends=True),
    }


def strip_old_markers(cells: list[dict]) -> list[dict]:
    kept = []
    for c in cells:
        if c.get("cell_type") == "markdown":
            src = c.get("source", "")
            if isinstance(src, list):
                src = "".join(src)
            if src.strip().startswith(MARKER):
                continue
        kept.append(c)
    return kept


def load(nb_name: str) -> dict:
    path = INFERENCE / nb_name
    with path.open() as f:
        return json.load(f)


def save(nb_name: str, nb: dict) -> None:
    path = INFERENCE / nb_name
    with path.open("w") as f:
        json.dump(nb, f, indent=1)
        f.write("\n")


def splice(nb: dict, explanations: dict[int, str]) -> None:
    """Insert markdown cells after the *original* code cells identified by
    their original index (pre-insertion). `explanations[i]` is the body text
    to add after the i-th cell of the original notebook.
    """
    original = strip_old_markers(nb["cells"])
    out = []
    for i, cell in enumerate(original):
        out.append(cell)
        if i in explanations:
            out.append(md_cell(explanations[i]))
    nb["cells"] = out


# ---------------------------------------------------------------------------
# Cerchie.ipynb  (7 original cells)
# 0 code  - load + ring-vs-monthly consistency check
# 1 md    - "Average danger by cerchia and month"
# 2 code  - per-km2 tables by cerchia/month
# 3 md    - "Visual diagnostics"
# 4 code  - plots (barh, city monthly, multi-metric, fallback)
# 5 md    - "Inferential Upgrade"
# 6 code  - Poisson GLM + bootstrap + chi-square seasonality
# ---------------------------------------------------------------------------

cerchie = {
    0: """
### Interpretation: data integrity check

Before any inference we verify that the two source tables are internally
consistent. For every `(year, month)` pair we compare the citywide total
crashes computed from `milan_crashes_monthly_cleaned.csv`
(`IncidentiMortali + IncidentiSoliFeriti`) with the sum across ring rows
in `milan_crashes_monthly_city_ring_cleaned.csv` (`Incidenti`).

**What to look for**

- `all_year_month_pairs_match = True` indicates perfect reconciliation,
  so downstream ring shares can be treated as a faithful decomposition of
  the citywide total.
- Any positive value in `mismatches_due_to_missing_values` flags months
  where one of the two tables is incomplete. For those months we fall
  back to `rings_total_crashes` when we build the analysis frame in the
  next cell, so the mismatch does not silently bias ring-level rates.
- `max_abs_delta_non_missing` quantifies the residual numerical gap once
  missingness is ignored; values of 0 mean the decomposition is exact.

This step is pre-inferential: it protects every subsequent normalization
and Poisson model from garbage-in errors. If a mismatch appeared here,
every per-km² rate and every IRR below would inherit that noise.
""",
    2: """
### Interpretation: area-normalized exposure measures

The step above answers a density question, not a count question.
Raw crash counts trivially rank the outer ring first because it is much
larger in km². Dividing by the official cerchia area converts each
variable to an **intensity** (events per km² per month), which is the
correct object to compare across zones of very different size.

**Statistical notes**

- *Normalization choice.* We divide by a fixed area (km²), not by
  population or kilometres travelled. So the results describe geographic
  pressure, not personal risk. A densely trafficked small ring can look
  very dangerous per km² even if the per-capita risk is modest.
- *Three metrics in parallel.* `fatal_incidents`, `total_incidents`,
  `non_fatal_proxy (Feriti)` are reported separately because their
  scales differ by roughly two orders of magnitude. Reading them in the
  same table would collapse the fatal signal.
- *Aggregation.* `avg_across_months_per_km2` is the monthly mean of the
  per-km² series; `range_max_min_per_km2` gives a first, descriptive
  proxy for seasonality strength (we formalize this with a chi-square
  test further down).
- *Resolved totals.* `resolved_total_crashes_per_km2` uses the fallback
  value from the rings table when the monthly file is missing, so the
  citywide monthly profile is not biased by holes.

**Reading the table**

The cerchia at the top of `diff_by_cerchia` is the highest-density zone
on that metric. The top row of `city_month_danger` is the
peak-exposure month across the full city. These two tables become the
descriptive backbone of the "geography of risk" narrative.
""",
    4: """
### Interpretation: visual diagnostics

The three panels are descriptive companions to the numerical tables
above.

**Horizontal bar charts (per km²).** Each panel ranks the four rings on
one metric. Because all three axes are densities, the visual ordering is
directly comparable across panels. A consistent top-ranked cerchia
across *total* and *non-fatal* suggests a general exposure effect; a
top-ranked cerchia on *fatal* that ranks lower on totals would instead
hint at a severity-specific pattern, which we test formally with the
Poisson model below.

**Citywide monthly profile.** The line over Jan–Dec uses the resolved
totals (monthly file, falling back to the rings sum where missing).
Peaks and troughs here are the raw seasonal pattern. The red/green dots
mark the peak and trough months; these will be re-tested for
statistical significance with the chi-square-vs-uniform test in the
final cell.

**Dual-axis monthly panels.** Fatal intensity is plotted on its own
smaller axis because its scale is ~100× below total incidents. Reading
them on one axis would flatten the fatal curve into a line that cannot
be distinguished visually.

**Fallback months plot.** Only renders when there were data holes. Each
bar is a month reconstructed from the rings table; the plot is a sanity
check that the fallback magnitudes are not outliers relative to normal
months. If a fallback bar were visually extreme, we would down-weight
its influence in downstream tests.
""",
    6: """
### Interpretation: formal inference on ring severity and seasonality

This cell upgrades the descriptive ring story into three formal
statistical objects.

**1. Bootstrap confidence intervals for per-incident severity rates.**
For each cerchia we resample monthly rows with replacement (n_boot =
4000) and compute the ratio `sum(Morti) / sum(Incidenti)` (×1000) and
`sum(Feriti) / sum(Incidenti)` on each bootstrap draw. Reporting the
2.5th and 97.5th percentiles gives a distribution-free 95% CI that
respects the clustered monthly structure, without assuming normality.
This is the **severity** view: deaths per 1,000 crashes, not deaths per
km².

**2. Poisson rate models with crash-count offset and month fixed
effects.** Formally we fit

```
log E[Morti]   = α + β_ring · Cerchia + β_month · C(month) + log(Incidenti)
log E[Feriti]  = α + β_ring · Cerchia + β_month · C(month) + log(Incidenti)
```

so ring coefficients are interpreted on the scale of **incidence-rate
ratios (IRR)** relative to the reference cerchia. The `offset =
log(Incidenti)` term means the outcome is deaths (or injuries) **per
crash**, absorbing exposure. The `C(month)` control removes confounding
by seasonality, so what remains is the ring's own severity signature.

We use HC3 robust standard errors, which are heteroscedasticity-robust
and perform well in small-to-moderate samples. Benjamini–Hochberg
correction across the three non-reference ring contrasts keeps the
family-wise false-discovery rate below 5%.

*How to read the IRR table:*
- `irr_vs_reference > 1` means severity is elevated vs the reference
  cerchia; `< 1` means it is reduced.
- The 95% CI excludes 1 whenever `q_value < 0.05`, so CI and
  significance are redundantly encoded.
- A large chi-square on `C(Cerchia)` (test of joint ring equality)
  formalizes "rings differ in severity even after controlling for how
  busy they are and which month it is."

**3. Chi-square test of monthly uniformity, by ring.** For each
cerchia we take the 12 monthly crash totals and test whether they are
consistent with the null of equal counts per month. The statistic is
`Σ (O_i − E_i)² / E_i` with 11 degrees of freedom, where `E_i = total /
12`. BH-adjusted p-values are reported. A highly significant chi-square
means that ring's crash calendar is structurally non-uniform — so
month-of-year is a real scheduling signal for that ring, not random
noise.

**Why these three together?** The Poisson IRRs answer "is this ring
unusually deadly?"; the bootstrap CIs bound how precise those severity
rates are; the seasonality chi-squares answer "should prevention be
timed differently per ring?" Together they justify the ring-and-season
prioritization in `findings.md`.
""",
}

# ---------------------------------------------------------------------------
# CrashDrugUse.ipynb  (7 cells)
# 0 md    - header
# 1 code  - load
# 2 code  - yearly aggregation + Milan wastewater wide pivot
# 3 code  - pairwise Pearson
# 4 code  - plots + z-score trend
# 5 md    - "Robustness Upgrade"
# 6 code  - perm raw / partial / diff / lag + LOO
# ---------------------------------------------------------------------------

crashdrug = {
    1: """
### Interpretation: data loading

We resolve the project root robustly (so the notebook runs whether the
kernel starts at the repo root or inside `notebooks/`), then load the
two pre-cleaned inputs produced by the cleaning notebooks:

- `milan_crashes_monthly_cleaned.csv` → monthly crash aggregates for
  Milan (fatal, injury-only, victims).
- `euda_wastewater_ww2026_all_cities_cleaned.csv` → EUDA (European
  wastewater) metabolite loads across many cities; we filter to Milan
  downstream.

At this point we only print row counts. The statistical chain has not
started — failing loudly here prevents downstream tests from running on
stale or partial data.
""",
    2: """
### Interpretation: yearly aggregation and panel construction

Because wastewater data is annual in this release, every crash row is
collapsed to the yearly level.

**Aggregation choices**

- `fatal_crashes`, `non_fatal_crashes`, `total_crashes` are **sums** of
  the monthly totals within a year; they preserve the count scale for
  correlation with the metabolite loads.
- Milan wastewater is subset by `City == "Milan"` (case-insensitive)
  and aggregated to the yearly mean per metabolite via `Daily mean`.
  Using the mean (not the sum) keeps units intact — picking sum would
  introduce a coverage-days artefact since campaigns vary year to year.
- The long-format `milan_yearly_long` is pivoted to wide so that each
  metabolite becomes a column named `drug_daily_mean_<slug>`. This is
  the object we correlate against crash metrics.

**Inner merge on `Year`.** `analysis_df` keeps only years present in
*both* sources. This is deliberate: it bounds every subsequent
correlation to the overlap window, which in this dataset is roughly 10–
14 years depending on the metabolite. With *n* this small, the
statistical power is limited and the risk of spurious correlations
through shared trends is high — a central motivation for the
robustness section later.
""",
    3: """
### Interpretation: raw pairwise Pearson correlations

For every `(crash_metric, metabolite)` pair with at least 5 shared
years we compute the Pearson `r`. Pearson measures *linear* association
on raw levels.

**Why this is only a starting point**

- Both sides are yearly time series. If crashes and a metabolite share
  a common trend (e.g. both trending down over a decade) the Pearson
  `r` will look strong mechanically, without any direct link. This is
  the classical trend-coupling trap; we address it in the robustness
  cell with partial correlation and first differences.
- With *n* between 5 and 14, sampling variance is very large. A raw
  `|r| = 0.6` is not surprising under the null for small samples; a
  naive two-tailed p-value without adjustment overstates evidence.
- We are computing many pairs in parallel (3 crash metrics × k
  metabolites). That is a multiple-testing problem; we apply
  Benjamini–Hochberg below.

`by_crash_summary` gives a per-crash-metric descriptive overview (how
many metabolites each crash column pairs with, and the maximum `|r|`
observed) to decide where to zoom in visually in the next cell.
""",
    4: """
### Interpretation: visual triangulation

The three plots are descriptive, not inferential.

**Top correlations bar chart.** Sorting by `|r|` exposes which
metabolite–crash pairs dominate the raw association ranking. A
consistently negative set (as we see with cocaine / cannabis) already
hints at shared downward trends across the decade.

**Heatmap.** The heatmap reveals block structure: metabolites that
correlate similarly with all crash metrics tend to be on the same
underlying trend. This is a visual cue that partial-correlation
controls will likely collapse many of the raw effects.

**Z-score trend chart for the top three metabolites vs total crashes.**
Standardizing each series to zero mean and unit variance puts crash
counts and metabolite loads on a common axis. When all lines slope
together (or together-reversed), Pearson `r` will be high
mechanically. The point of the plot is to let the reader *see* whether
short-run wiggles align or whether everything is just riding a single
multi-year drift.

None of these panels should be read as causal evidence. They set up
the robustness tests that follow.
""",
    6: """
### Interpretation: robustness battery

This cell stress-tests every crash–metabolite pair with four
progressively stricter criteria, and reports how many survive each.

**1. Permutation p-values on the raw Pearson `r`.** We shuffle the
metabolite column 8000 times and count the fraction of random `|r|`
that meet or exceed the observed `|r|`. Because the permutation
distribution makes no normality assumption and is honest to small-*n*
sampling variability, it is safer than a t-based p-value when *n ≈
10*.

**2. Year-controlled partial correlation.** We regress both `x` and
`y` on `Year` (OLS) to obtain residuals, then correlate the residuals.
This isolates the *short-run* co-movement by removing the linear
secular trend. Pairs whose raw effect is trend-coupling (the dominant
risk here) typically lose significance here.

**3. First-difference correlation.** We correlate the yearly changes
`Δx = x_t − x_{t−1}` with `Δy`. This is the strictest test for
contemporaneous co-movement: any shared mean, trend, or slow level
shift is differenced away. If `p_diff < 0.05`, the variables move
*together year-over-year*, which is much more consistent with a real
short-run relationship.

**4. One-year lag check.** We shift the metabolite series forward by
one year and correlate with crashes. Significance here would suggest
directional timing (drug marker year *t* predicts crashes year *t+1*),
though with *n ≈ 10* the evidence is fragile.

**Benjamini–Hochberg correction.** We apply BH separately to the
`p_raw`, `p_partial`, and `p_lag` families. The q-columns control the
false-discovery rate at 5% within each family.

**`robust_signal` flag.** A pair is marked robust **only if** its
year-controlled p survives BH and its first-difference p is below
0.05. This combined criterion is intentionally strict — it is the
threshold we trust before claiming a real link in the project.

**Leave-one-year-out sign stability for the strongest raw pair.** For
the pair with the smallest `q_raw`, we re-estimate the raw `r` leaving
one year out at a time and compute the share of leave-one-out fits
whose sign matches the full-sample sign. A `sign_consistency = 1.0`
tells us no single year is flipping the direction — so the raw effect
is not driven by one leverage point. Even so, sign stability does not
rescue a pair that failed the partial / first-difference tests: it is
diagnostic, not exculpatory. The histogram shows the spread of
leave-one-out `r` values around the full-sample estimate (red dashed
line).
""",
}

# ---------------------------------------------------------------------------
# Fleet.ipynb  (12 cells)
# 0 md    - header
# 1 code  - load
# 2 code  - aggregation + exposure rates
# 3 code  - z-score trends
# 4 code  - perm Pearson/Spearman (raw)
# 5 code  - partial (year) + first-difference
# 6 code  - period sensitivity
# 7 code  - slope permutation + bootstrap CI
# 8 code  - print key conclusions
# 9 md    - "Interpretation Guide"
# 10 md   - "Robustness Upgrade"
# 11 code - BH correction + post-2020 interaction + rolling-window
# ---------------------------------------------------------------------------

fleet = {
    1: """
### Interpretation: data loading

Two inputs are read: `milan_vehicle_fleet_cleaned.csv` (ACI fleet
counts by vehicle category, yearly) and
`milan_crashes_monthly_cleaned.csv` (Milan monthly crash aggregates).
Failing early (`FileNotFoundError`) keeps the statistical pipeline
from running on stale intermediates.
""",
    2: """
### Interpretation: building the yearly exposure panel

**Collapsing to yearly.** Fleet data is released annually, so the
unit of analysis is the year. Monthly crashes are summed by year.

**Constructing exposure-adjusted rates.** Absolute crash counts grow
with the fleet mechanically. To isolate risk changes we build:

- `crashes_per_10k_fleet = total_crashes / fleet_total · 10,000`
- `fatal_crashes_per_100k_fleet` (rarer event, scaled by 100,000)
- `deaths_per_100k_fleet`
- `injuries_per_10k_fleet`

These rates are the objects on which long-run trend tests later
produce the "safer per exposure unit" conclusion. Correlating raw
counts instead would conflate fleet growth with actual risk.

**Fleet composition features.** We also derive `car_share` and
`motorcycle_share`. Shares are scale-free and allow us to ask: even if
the total fleet changes, does the *mix* of vehicles predict crash
outcomes? The answer drives the later post-2020 regime-shift test.

**Inner merge on Year.** We keep only years present in both tables;
`missing_years` flags any internal holes (important because
first-differences need contiguous years).
""",
    3: """
### Interpretation: visual sanity check of the trends

Every series is converted to z-scores so they can share one axis. What
to look for:

- **Co-moving lines** suggest a common long-run trend. If, for
  example, `fleet_total` and `total_crashes` trace similar shapes,
  that is consistent with Pearson `r` being high mechanically,
  regardless of whether the relationship is causal.
- **A divergence post-2020** in any series is a first visual flag for
  the regime-shift diagnostic run at the bottom of the notebook.
- **Turning points** (where a series reverses direction) help identify
  rolling-window structural breaks before we formalize them.

This is descriptive. It does not measure association strength and is
not a substitute for the permutation tests below.
""",
    4: """
### Interpretation: raw Pearson and Spearman with permutation p-values

For every fleet × crash pair we compute:

- **Pearson `r`** (linear association on levels)
- **Spearman `ρ`** (association on ranks — robust to outliers and
  monotone-but-non-linear structure)

and a **permutation p-value** (12,000 shuffles of `y`). The observed
`|r|` is compared against the null distribution of `|r|` under random
pairing. With *n ~ 15–19* this is much more faithful to small-sample
behaviour than a t-based p.

**Why report both Pearson and Spearman?** If the two agree, the
effect is robust to functional form. If Pearson is large but Spearman
is modest, we should suspect a handful of leverage years driving the
result.

**Important caveat.** Significance at this stage should be read as
"raw association", not causal. Almost every pair is a yearly time
series with a secular trend; the partial-correlation and
first-difference tests in the next cell are the required next step.
""",
    5: """
### Interpretation: trend control and short-run co-movement

**Partial correlation, controlling for Year.** We regress both `x`
and `y` on `Year` (OLS), take residuals, and compute `r` on the
residuals. The permutation p-value now asks "is there association
*beyond* what Year alone explains?" If the raw `r` is driven by the
shared decade-long drift, it collapses here.

**First differences, annualized.** We compute `Δx_t / gap_t` and
`Δy_t / gap_t` (the division by gap handles missing years so that one
unit of change is one year of change). We then correlate the yearly
changes. This is a stricter test: it asks whether crashes and fleet
co-move *year-over-year*, a much stronger signal than a shared
long-run slope.

**Reading the two tables together.**

- Large raw `r` + null partial `r` ⇒ trend coupling, not a direct
  link.
- Partial `r` significant but first-difference null ⇒ partial evidence
  for a slow, non-trivially-trend-driven relationship (should still be
  reported cautiously).
- Partial `r` significant **and** first-difference significant ⇒ the
  pair moves together on both slow and fast timescales. This is the
  highest standard of evidence available from this data alone, and it
  is the criterion encoded in `robust_evidence` below.
""",
    6: """
### Interpretation: sensitivity by time period

We repeat the year-controlled partial correlation on three
overlapping windows: full sample, pre-COVID, and 2010+. Two lessons:

- **Stability across windows** → the partial relationship is a
  structural feature of the data, not an artefact of a specific
  pandemic year or a single decade.
- **Sign flips or significance flips across windows** → the
  relationship is *regime-dependent*. Any pre-2020 coefficient should
  not be extrapolated to the post-2020 regime. In this panel,
  `motorcycle_share` is the clearest example of this behaviour (see
  the formal interaction test in the last cell).

This is a conservative audit: if a relationship is real and
time-invariant, it should survive most reasonable period choices.
""",
    7: """
### Interpretation: long-run risk trends (exposure-adjusted)

For four exposure-adjusted rates we fit a linear regression
`rate ~ Year` and report:

- **Slope per year** — the annual change in the rate (e.g. crashes
  per 10,000 vehicles per year). Negative slopes mean safer per
  exposure unit.
- **Permutation p-value on the slope** (15,000 shuffles of `y`): the
  probability of observing a slope at least as large in absolute value
  under the null that Year and rate are independent.
- **Bootstrap 95% CI on the slope** (5,000 draws with replacement
  over rows). A CI that excludes zero is consistent with the
  permutation significance and is robust to normality assumptions.

The twin plot shows two of these rates with the fitted OLS line for
visual confirmation. A consistently negative slope with CI below zero
is the strongest, most defensible fleet-level finding in the
notebook: system-level risk per exposure unit has fallen over the
observation window.
""",
    8: """
### Interpretation: conclusion snapshot

This cell turns the raw and trend-adjusted tables into narrative
bullet points:

- The raw correlations (e.g. `total_crashes` vs `fleet_cars`) are
  reported for transparency only.
- The trend-adjusted partials are the policy-relevant numbers when
  they survive the first-difference and BH checks that follow.
- The period-sensitivity table is reproduced to expose regime
  instability (critical for `motorcycle_share`).
- The exposure-adjusted slope figures are re-surfaced because they
  are the most robust fleet-era result.

This is a preview; the formal multiple-testing corrections and the
regime-shift diagnostic are applied in the next code cell.
""",
    11: """
### Interpretation: multiple-testing control and regime shift

**Benjamini–Hochberg correction.** Three families of tests were run
(raw, partial, first-difference). For each family we convert
per-pair p-values to BH q-values and flag `q < 0.05`. The `robust
_evidence` flag requires **both** BH significance on the partial `r`
**and** sign stability between raw and partial — i.e. the association
is not flipped by detrending and is genuinely non-trend. In this
panel, the BH-survival count at the partial level collapses from
raw-significant dozens to zero, which is why the notebook concludes
that most fleet–crash correlations are trend artefacts.

**Post-2020 regime test.** We fit

```
total_crashes ~ Year + motorcycle_share + post2020 +
                motorcycle_share:post2020
```

with HC3 robust standard errors. The interaction term
`motorcycle_share:post2020` is the formal answer to "did the slope
relating fleet composition to crashes change after 2020?". A
significant coefficient (positive or negative) means the two eras
have statistically different relationships and pre-2020 estimates do
not transfer.

**Rolling 8-year correlation.** For each 8-year window we compute
`corr(motorcycle_share, total_crashes)`. A visibly shrinking (or
sign-flipping) curve is a non-parametric mirror of the interaction
test: it confirms visually that the association is weakening, which
is exactly what the regime-shift model reports numerically.
""",
}

# ---------------------------------------------------------------------------
# CrashType.ipynb  (23 cells)
# code cells are at indices 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21
# ---------------------------------------------------------------------------

crashtype = {
    1: """
### Interpretation: library imports and global settings

We pin a seed, fix pandas display precision, and import the full
inference stack up front:

- `scipy.stats` for classical tests (chi-square, Kruskal–Wallis,
  Mann–Whitney, Spearman, bootstrap).
- `statsmodels` for Poisson GLMs, OLS with HC3 robust SEs, VIF, and
  BH multiple-testing correction.
- `sklearn` for the predictive benchmark (multinomial logit and
  random forest) with time-blind CV now and a temporal holdout at the
  end.
- `seaborn` / `matplotlib` for exploratory plots.

Setting `np.random.seed(42)` makes every bootstrap, cross-validation
split, and permutation reproducible.
""",
    3: """
### Interpretation: data load and raw schema inspection

Four cleaned tables are loaded from `data/processed/`:

- `nature` — crashes by nature (`NaturaIncidente`) at monthly
  resolution. This is the classification target.
- `vehicles` — crashes by number of vehicles involved (1, 2, 3, 4,
  5, 6, 7+). This will become a vehicle-mix feature set.
- `monthly` — citywide monthly totals (fatal and injury-only
  incidents, deaths, injuries). This gives exposure and severity
  context.
- `zone` — crashes by Municipio. We convert this into a
  concentration index (Herfindahl–Hirschman).

Inspecting `nature["NaturaIncidente"].value_counts()` shows the class
distribution of the target. Strong imbalance here is important: it
directly shapes downstream choices (class weights in the model, the
decision to report macro-F1, and the interpretation of the confusion
matrix).
""",
    5: """
### Interpretation: cleaning and schema normalization

Two types of issues are handled:

1. **Type hygiene.** Dates are coerced to `datetime64` and all count
   columns to numeric. Coercion errors are turned into NaN rather
   than exceptions, so we can *see* the cleaning gap.
2. **Target normalization.** `NaturaIncidente` is renamed to
   `crash_type` and stripped of whitespace so that downstream
   groupbys do not over-split categories because of trailing spaces.

**Rows removed** during dedup and NaN-dropping are reported
explicitly. If a large fraction of rows were dropped here, every
test below would be biased toward the surviving subset; small drops
are acceptable.

`coverage` (min, max, unique month) confirms the temporal span of
the panel. The number of unique crash types sets the dimensionality
of the later chi-square and classification problems.
""",
    7: """
### Interpretation: feature engineering

We build four feature families around each crash type × month row.

- **Exposure and severity context** (from `monthly`):
  `IncidentiTotali`, `IncidentiMortali`, `MortiTotaliMese`,
  `FeritiTotaliMese`. These give the citywide baseline against which
  each crash type's share and fatality rate are measured.
- **Vehicle mix** (from `vehicles`): `share_1v`, `share_2v`,
  `share_3plus`. Shares are scale-free and explicitly sum to ~1 — so
  we drop `share_3plus` in the VIF check later to avoid
  collinearity.
- **Spatial concentration** (`zone_hhi`): the
  Herfindahl–Hirschman index, `Σ s_i²`, where `s_i` is a
  Municipio's share of monthly crashes. An HHI close to 1 means
  crashes are concentrated in few Municipi; close to 0 means
  diffuse. This is a well-understood index from economics; using
  it here is principled because it gives a single number for
  spatial inequality per month.
- **Seasonality proxies** (`month`, `year`, `is_weekend_proxy`,
  `season`). `season` is a four-level categorical used in the
  chi-square tests; `month`/`year` feed the residualization for
  partial correlations.

We also derive the three outcomes used downstream:

- `type_share = Incidenti / IncidentiTotali` — the relative
  prevalence of this crash type that month.
- `injury_rate = Feriti / Incidenti` — injuries per incident.
- `fatal_rate_1000 = 1000 · Morti / Incidenti` — deaths per 1,000
  incidents; the per-crash mortality scaling.

**Tertile binning** via `safe_qbin` converts the continuous severity,
vehicle-mix and spatial-concentration scores into categorical
regimes (low / medium / high). This is intentional: categorical
regimes feed the chi-square tests in cell 11, where a continuous
Cramér's V would not apply.
""",
    9: """
### Interpretation: exploratory association between crash type and context

The four-panel figure is descriptive:

- **Total incidents by crash type** — ranks the classes. The
  heavy-tailed distribution here is why later modelling needs
  class-balanced weighting.
- **Monthly share distribution** — boxplots of `type_share` per
  class quantify both level and variability. A crash type with a
  small median but a long upper tail is one that spikes in specific
  months.
- **Fatality rate per 1,000 incidents** — violin plots reveal
  asymmetry and heavy tails in per-crash mortality. Classes with a
  high median here will be the ones flagged by the Poisson IRR
  model below.
- **Feature means heatmap** — a compact view of "which crash types
  look similar in context space". Tight clustering on this heatmap
  usually implies two classes will be confusable in the classifier.

The `pairplot` on a random sample of 800 rows lets us eyeball
bivariate structure; if two metrics are monotone on each class
independently, later rank-based tests will be more powerful than
level-based Pearson.
""",
    11: """
### Interpretation: formal association tests across crash types

Two test families run here, each with BH correction.

**Categorical × crash type (chi-square + Cramér's V).** For
`season`, `multi_vehicle_regime`, `location_cluster`, `severity
_level` we build a contingency table with `crash_type`, run Pearson
chi-square, and compute Cramér's V as the effect size,

$$V = \\sqrt{\\frac{\\chi^2/N}{\\min(r-1, k-1)}}$$

which is bounded in `[0, 1]` (0 = independence, 1 = perfect
dependence). The chi-square p answers "are the two categorical
variables independent?"; Cramér's V tells us whether a significant
effect is also practically large.

**Continuous metrics by crash type (Kruskal–Wallis).** We use the
rank-based Kruskal–Wallis H rather than ANOVA F because crash
metrics are non-normal and right-skewed. We also report a
variance-decomposition eta-squared, `SS_between / SS_total`, as a
rough effect-size companion, so a significant H with tiny eta² is
correctly flagged as "real but small".

**Pairwise Mann–Whitney U post-hoc.** When the overall K–W is
significant, we compare each pair of crash types. The **rank-biserial
correlation**, `r_rb = 1 − 2U / (n_a · n_b)`, is the effect-size
metric (`|r_rb|` close to 1 means one class almost always ranks
higher than the other on that metric).

**BH correction**  is applied independently to the three families
(categorical, numeric, post-hoc) so we control FDR within each
semantically-homogeneous test set rather than across heterogeneous
tests.
""",
    13: """
### Interpretation: multivariate classification benchmark

We benchmark two classifiers under 5-fold stratified CV:

- **Multinomial logistic regression** — interpretable linear model,
  gives us odds ratios per feature per class.
- **Random forest** — non-linear baseline; if it substantially
  beats the logit, there is interaction/non-linearity the linear
  model cannot capture.

**Pipeline design.** Median imputation + standard scaling for
numerics, most-frequent imputation + one-hot for categoricals. Putting
imputation inside the pipeline (not before CV) prevents leakage from
the holdout fold into training fold imputation statistics.

**Scoring choice.** We report both `macro_f1` and `accuracy`. In
imbalanced multi-class settings accuracy is misleading (a classifier
predicting the dominant class does fine on accuracy and horrible on
minority recall). Macro-F1 is the unweighted average of per-class F1,
so every class contributes equally — the right metric when we care
about recovering minority crash types.

**Model selection.** The better macro-F1 model is retrained on a
random stratified holdout split. The classification report and
confusion matrix tell us *which* classes are predictable: diagonals
close to `support` mean good recall; big off-diagonals mean the two
classes share context-space and the predictor confuses them.

**Logit coefficients.** For each class we print the eight features
with the largest absolute coefficients along with `odds_ratio =
exp(coef)`, interpretable as "each 1-SD change in this feature
multiplies the relative odds of this crash type by `odds_ratio`."
These are *descriptive of the classifier*, not causal.

**Important:** CV here is random, not temporal. The temporal holdout
further down is the honest test of generalization.
""",
    15: """
### Interpretation: assumption checks and re-specification loop

This is the "iteration loop" step mandated by the analysis plan.

**Class balance.** `y.value_counts(normalize=True)` is printed so the
reader can judge whether minority-class F1 numbers are trustworthy.
Highly imbalanced targets can drive macro-F1 down even when the model
is doing its job on common classes.

**Multicollinearity (VIF).** For each numeric feature we compute the
variance inflation factor,

$$\\mathrm{VIF}_j = \\frac{1}{1 - R_j^2}$$

where `R_j^2` is the R² from regressing feature `j` on the others.
Rule of thumb: VIF > 5 signals moderate collinearity, > 10 severe.
We drop `share_3plus` up front because the three vehicle shares sum
to 1 by construction — that is a structural dependence, not a
statistical one, and it would otherwise return VIF = ∞.

**Re-specification: log transform.** Count columns
(`IncidentiTotali`, etc.) are strongly right-skewed. `log1p` is
monotone, handles zeros, and compresses the right tail. We re-fit
the logit on the log-transformed features under the same CV and
compare macro-F1. We keep whichever specification wins; the
performance delta is printed so the choice is auditable.

This loop enforces honesty: we publish the model *after* checking
its assumptions, not before.
""",
    17: """
### Interpretation: effect sizes with trend/seasonality controls and bootstrap CIs

This cell produces the paper-grade correlation table.

**Detrending with trend + harmonic seasonality.** Each crash type's
time series is residualized on:

- a constant,
- a linear trend on month index,
- two sinusoidal pairs at periods 12 and 6 months (captures annual
  and semi-annual seasonality).

Then we compute the Spearman `ρ` on the residuals. This is a
*partial rank correlation* that removes both long-run drift and
recurring seasonal patterns — the two biggest confounders in monthly
panels. We also compute a "trend only" residualization
(`rho_partial_trend_only`) so the reader can see whether seasonality
is driving any of the association.

**First-difference Spearman (`rho_diff`).** Correlating the
year-over-year (month-over-month in this panel) changes is a
separate, independent robustness test. It survives only when the two
series co-move on the fast timescale.

**Bootstrap 95% CI on the partial Spearman.** 600 resamples with
replacement; the 2.5th and 97.5th percentiles are the CI. This is
non-parametric and honest to the small effective sample size within
each crash type × metric pair.

**`robust_flag`.** A correlation is reported as *robust* only if all
three conditions hold:

- BH-corrected `q_partial < 0.05` (trend + season adjusted),
- raw `p_diff < 0.05` (holds under first-differencing),
- `|ρ_partial| ≥ 0.2` (minimum practically-meaningful effect size).

The `stable_sign` column checks whether the sign of the partial
matches the trend-only-partial — a further consistency diagnostic.

This is the most stringent filter in the notebook. Whatever survives
it is the set of crash-type × context links we are willing to
publish.
""",
    19: """
### Interpretation: rate-ratio modeling and consolidated findings

We fit two Poisson rate models with crash-count offset:

```
log E[Morti]   = α + β_ct · C(crash_type) + log(Incidenti)
log E[Feriti]  = α + β_ct · C(crash_type) + log(Incidenti)
```

so coefficients are **incidence-rate ratios** relative to the
alphabetically-first crash type (reference class). The offset means
the outcome is deaths (or injuries) *per crash*, so IRRs describe
severity per incident, not total volume. HC3 robust standard errors
guard against heteroscedasticity in the monthly panel.

Each IRR table reports:

- `estimate = exp(coef)` — the multiplicative severity ratio vs the
  reference class.
- 95% CI from `exp(confint)`.
- p-value and BH q-value across the set of non-reference classes.
- `direction` (`higher_than_reference` or `lower_than_reference`).
- `supported = q < 0.05`.

**Consolidated `findings_table`.** We concatenate:

- *Partial Spearman* findings (the `robust_corr` rows from cell 17),
- *Poisson IRR* findings (death and injury rates).

This is the single artefact the writeup quotes: every row is either
a robust detrended correlation or a corrected rate-ratio, and every
row carries a direction, effect size, CI, and q-value.

The textual `summary_points` lines highlight the strongest robust
correlation and the highest corrected death and injury IRRs, which
feed directly into the presentation narrative.
""",
    21: """
### Interpretation: temporal holdout validation

Random k-fold CV (above) is too optimistic for time-indexed data
because future information leaks into the training fold. This cell
enforces a **temporal holdout**:

- `year_cutoff` = 80th percentile of the observed years.
- Training set: years ≤ cutoff.
- Test set: years > cutoff.

We refit the selected specification on the training slice and
predict the holdout years. The classification report on the holdout
gives the **honest** out-of-period performance. If macro-F1 here is
much lower than in random CV (it typically is), the interpretation
is that crash-type composition drifts over time and the current
feature set does not fully capture that drift.

The orange confusion matrix localizes the failure modes: classes
with near-zero recall on the holdout are the ones whose prevalence
or context changed materially after the cutoff year. This number,
not the random-CV number, is what we should quote when deciding
whether the classifier is fit for forecasting.
""",
}


def main() -> None:
    cases = [
        ("Cerchie.ipynb", cerchie),
        ("CrashDrugUse.ipynb", crashdrug),
        ("Fleet.ipynb", fleet),
        ("CrashType.ipynb", crashtype),
    ]
    for name, explanations in cases:
        nb = load(name)
        splice(nb, explanations)
        save(name, nb)
        print(f"updated {name}: inserted {len(explanations)} explainer cells")


if __name__ == "__main__":
    main()
