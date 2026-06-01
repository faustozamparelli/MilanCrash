# plan.md | Forward Roadmap

This file lists work that is still genuinely ahead of the current project. Completed findings belong in `findings.md`, not in the future plan.

## Immediate Extensions

### Weather overlay: temperature, precipitation, and crash counts

- **Question.** Do monthly crashes covary with Milan monthly temperature and precipitation after controlling for year, ring, and seasonality?
- **Why it matters.** Weather is the main missing confounder for the seasonality story. If weather absorbs much of the ring-calendar pattern, the policy interpretation changes.
- **Data needed.** New monthly Milan weather data from ARPA Lombardia, Meteostat, or Copernicus ERA5: `Year`, `month`, mean temperature, maximum temperature, precipitation, and rain days.
- **Method.** Extend the count model with weather covariates, compare month and ring-seasonality tests before and after adding weather, and use first-difference checks as a robustness screen.
- **Deliverable.** A coefficient table for weather IRRs with CIs and q-values, plus a before/after comparison of the seasonal interaction evidence.

### Day-of-week and holiday effects

- **Question.** Is there a weekend or holiday crash premium in Milan, and does it differ by ring or crash type?
- **Why it matters.** Monthly data answers "which month?", but enforcement and prevention campaigns are often scheduled by day.
- **Data needed.** Daily-resolution crash data; the current cleaned crash tables are monthly.
- **Method.** Poisson or negative-binomial GLM with day-of-week, holiday, school-term, ring, and optional weather controls.
- **Deliverable.** A ring-by-day table of incident-rate ratios with CIs and BH-adjusted significance flags.

### Vulnerable-road-user indicator

- **Question.** Can we construct a compact index for vulnerable-road-user exposure from pedestrians, cyclists, and motorcycles?
- **Why it matters.** It would connect the crash-type severity result to the geography and fleet analyses with one presentation-ready exposure metric.
- **Data needed.** Existing processed crash and fleet data; a richer ring-by-crash-type table would improve it.
- **Method.** Build a weighted index with transparent components or PCA weights, then validate against fatal-crash and injury outcomes with year controls.
- **Deliverable.** Yearly index values, component/loadings table, and controlled association tests.

## Policy Evaluation

### Speed cameras, Zone 30, Area C, Area B, and other local policies

- **Question.** Did targeted Milan road-safety policies change crash counts, crash density, or per-crash severity in treated areas relative to controls?
- **Why it matters.** This moves the project from descriptive risk mapping to policy evaluation.
- **Data needed.** Policy start dates, geographic scope, and enforcement intensity for speed cameras, Zone 30 areas, Area C, Area B, or comparable interventions.
- **Method.** Difference-in-differences or event-study models with treated and control zones; use pre-trend diagnostics and placebo intervention dates.
- **Deliverable.** Event-time coefficient plots, average treatment-effect estimates, and clear non-causal caveats when assumptions are weak.

### Interrupted time series for specific enforcement changes

- **Question.** Did a dated enforcement or mobility-policy change create a level or slope change in Milan crash outcomes?
- **Why it matters.** It gives a stronger design than raw correlation when a precise intervention date exists.
- **Data needed.** A credible intervention date and daily or monthly crash outcomes around it.
- **Method.** Segmented regression with seasonality, trend, autocorrelation-robust standard errors, and placebo dates.
- **Deliverable.** Pre/post level and slope estimates with confidence intervals and placebo comparisons.

## Spatial And External Expansion

### Zone-level risk and small-area smoothing

- **Question.** Which Municipi have elevated crash risk after accounting for expected rates and small-area noise?
- **Why it matters.** Zone-level outputs are more actionable than broad rings.
- **Data needed.** Existing Municipio crash data plus official Municipio boundary geometries.
- **Method.** Spatial Poisson or empirical-Bayes smoothing; optionally compare with BYM-style spatial models.
- **Deliverable.** A ranked table and map of smoothed exceedance probabilities.

### Road-network and infrastructure features

- **Question.** Are ring or zone risk differences explained by arterial density, intersection complexity, speed-limit mix, or signalized crossings?
- **Why it matters.** It tests whether observed geography is a proxy for measurable built-environment mechanisms.
- **Data needed.** OpenStreetMap extracts, speed-limit data, and intersection/signal features.
- **Method.** Add infrastructure summaries to existing ring or zone models and compare before/after coefficients.
- **Deliverable.** A coefficient table showing how much ring effects change after infrastructure controls.

### Multi-city expansion

- **Question.** Do Milan's geography, seasonality, and severity patterns generalize to other Italian or European cities?
- **Why it matters.** It separates Milan-specific evidence from broader urban-road-safety regularities.
- **Data needed.** Comparable monthly crash data, spatial partitions, population or area denominators, and policy metadata for other cities.
- **Method.** Harmonized panel models with city fixed effects, city-specific seasonal harmonics, and cross-city robustness checks.
- **Deliverable.** A multi-city comparison table of crash density, severity, annual amplitude, and peak month.

## Project Quality

- Add a reproducible notebook execution target once notebook root-resolution is consistent across local and `nbconvert` runs.
- Move repeated statistical helpers into `scripts/inference_utils.py` when a second notebook needs the same helper.
- Add units and short legends to result tables before the final presentation pass.
