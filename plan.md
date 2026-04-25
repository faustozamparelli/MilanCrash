# plan.md | Next Analyses and How to Run Them

This is a forward-looking to-do for the project. Each item lists:

- **Question** — the analytical question.
- **Why it matters** — the decision or narrative it would sharpen.
- **Data needed** — whether we already have it in `data/processed/` (noted in parentheses) or would need to ingest new data.
- **Method** — the statistical or modelling approach, with emphasis on inference tools the project already uses (permutation, BH, Poisson GLM with offset, bootstrap CIs, partial correlation, first differences).
- **Falsifiable output** — what a successful deliverable looks like.

The items are grouped by strategic priority: **Tier 1** are high-value, low-new-data, fast; **Tier 2** need modest new data or a non-trivial modelling step; **Tier 3** are exploratory or depend on external releases.

---

## Tier 1 | High value, data already on disk

### 1.1 Spatio-temporal interaction: does seasonality differ by ring in amplitude, phase, or both?

- **Question.** The Cerchie notebook already shows seasonality is significant in every ring, but does the *shape* (peak month, amplitude) differ? The outer ring chi2 is 13x the Entro chi2 — is that just amplitude or is the peak on a different month?
- **Why it matters.** Turns the current "ring-specific calendar" suggestion into a concrete campaign timing: which month in which ring.
- **Data needed.** `milan_crashes_monthly_city_ring_cleaned.csv` (already available).
- **Method.**
  - Fit Poisson GLM with `log(area_km2)` offset and `Cerchia * sin(2 pi month / 12) + Cerchia * cos(2 pi month / 12) + Cerchia * sin(2 pi month / 6) + Cerchia * cos(2 pi month / 6)` to model annual and semi-annual cycles.
  - Joint Wald test on the interaction block to confirm "ring changes the seasonal shape".
  - Post-estimation: convert `(sin, cos)` coefficients per ring to `(amplitude, phase)` via `sqrt(a2+b2)` and `arctan2(a,b)`, with delta-method or bootstrap CIs.
- **Falsifiable output.** A 4-row table: ring x {annual amplitude, annual peak month, semi-annual amplitude, semi-annual peak month, p on ring x month interaction}.

### 1.2 Day-of-week and holiday effects (monthly panel already aggregates these away — raw daily needed)

- **Question.** Is there a weekend risk premium in Milan and does it differ by ring or crash type?
- **Why it matters.** The current project answers "which month?" but not "which day?". Day-of-week is the most actionable timing variable for enforcement and campaign scheduling.
- **Data needed.** Daily-resolution crash dataset. The current `milan_crashes_monthly_cleaned.csv` has already been aggregated; we would need to rerun the cleaning pipeline from raw Comune di Milano open-data at daily granularity, or request a daily export.
- **Method.**
  - Poisson GLM with `log(exposure)` offset (use fleet_total as coarse exposure, or VKT if obtained).
  - Calendar covariates: day-of-week dummies, holiday indicator, school-term indicator, Italian public holiday calendar, and optional weather (see 1.6).
  - BH correction across the 7 day dummies x rings.
- **Falsifiable output.** A heatmap of day-of-week IRRs by ring, with CIs and BH flags.

### 1.3 Decompose Investimento pedone by ring and month

- **Question.** The CrashType notebook shows pedestrian crashes have an IRR of ~7 for deaths per crash. Which rings and months drive this?
- **Why it matters.** Pedestrian safety is Milan's single largest per-crash risk factor. Knowing where and when it concentrates turns it into a location-based intervention brief.
- **Data needed.** Would need a *nature x ring* or *nature x zone* cross-tab at monthly resolution. The current `nature` dataset is citywide-monthly; the current `zone` dataset is zone-monthly but without crash type. A join on the raw Comune data at a finer granularity is required.
- **Method.**
  - Once the joint dataset exists, fit two Poisson models:
    1. `Morti ~ Cerchia + month + log(Incidenti pedestrians)` (offset on pedestrian incidents only).
    2. Same with `Incidenti pedestrians ~ Cerchia + month + log(area_km2)`.
  - Combined interpretation: where are pedestrian incidents most frequent per km2, and where are those incidents most deadly per crash.
- **Falsifiable output.** A heatmap (ring x month) of pedestrian fatality IRR with BH flags, plus a ranked short-list of "top-5 ring x month cells" for intervention.

### 1.4 Multi-vehicle regime and crash type — directional link via causal ordering

- **Question.** The CrashType notebook showed `share_2v` is strongly associated with Scontro frontale-laterale (partial rho = 0.60). Is this a tautology (more 2-vehicle months mean more 2-vehicle collisions) or does it carry information?
- **Why it matters.** A definitional link is not a finding; a non-definitional link could help forecast crash-type composition.
- **Data needed.** Already on disk.
- **Method.**
  - Granger-style test in first differences: does `share_2v_{t-1}` predict `share_scontro_frontale_laterale_t` beyond the contemporaneous association?
  - Because 2-vehicle collisions are a definitional subset of 2-vehicle months, also compute the partial rho on *residuals after removing the mechanical identity*: regress each series on `incidenti2veicoli / IncidentiTotali` and correlate the residuals.
  - Report both rho values; if the residual rho collapses, the finding is definitional.
- **Falsifiable output.** Before/after rho table with interpretation (definitional vs informative) and a one-paragraph note.

### 1.5 Vulnerable-road-user indicator: construct and validate

- **Question.** We do not currently have a single index for "vulnerable-road-user exposure" (pedestrians, cyclists, motorcyclists). Can we derive one from the existing columns and show it is significant?
- **Why it matters.** Gives a single handle for the presentation that ties together pedestrian IRR (CrashType), motorcycle share (Fleet), and ring density (Cerchie).
- **Data needed.** Already on disk; optionally enrich with ACI vehicle counts (already in `milan_vehicle_fleet_cleaned.csv`).
- **Method.**
  - Define `vru_index_t = (motorcycle_share_t * w1) + (pedestrian_crash_share_t * w2) + (bike_share_t * w3)` where `w_i` are PCA weights fit on yearly data.
  - Validate by checking that `vru_index` correlates (year-controlled partial) with `fatal_crashes_per_100k_fleet` at the expected sign.
- **Falsifiable output.** A yearly series of `vru_index`, its first principal-component loading table, and a partial-correlation table against each outcome.

### 1.6 Weather overlay: temperature, precipitation, and crash counts

- **Question.** Do monthly crashes covary with Milan monthly temperature and precipitation after controlling for year and ring?
- **Why it matters.** Weather is the canonical missing confounder in seasonality analyses. If weather absorbs the ring-month interaction, the "ring-specific calendar" recommendation weakens.
- **Data needed.** New: Milan monthly weather series from ARPA Lombardia (public), Meteostat, or Copernicus ERA5. A single CSV (year, month, tmean, tmax, precip, rain_days) would suffice.
- **Method.**
  - Extend the Poisson GLM with `C(Cerchia) + C(month) + temperature + precip + offset(log(Incidenti or area))`.
  - Compare chi2 on `C(month)` before and after adding weather. A substantial reduction means weather is mediating season.
  - First-difference correlation between monthly weather and ring-specific crash rates for a second independent check.
- **Falsifiable output.** A two-column coefficient table (temperature and precipitation IRRs, with CIs and BH q) and a before/after chi2 comparison for `C(month)`.

### 1.7 Are the four rings the right partition? A data-driven regrouping.

- **Question.** The four rings are administrative. If we clustered monthly ring patterns by their statistical signature (density, severity, seasonality shape), would we get a different partition?
- **Why it matters.** It would test whether the administrative rings are also the *statistical* units of risk. If not, we should recommend a data-driven zoning.
- **Data needed.** `milan_crashes_by_zone_cleaned.csv` (Municipio-level) + `milan_crashes_monthly_city_ring_cleaned.csv`.
- **Method.**
  - Build per-zone time-series features: mean incidents/km2, deaths/crash, amplitude and phase of annual cycle, share of pedestrian crashes.
  - Standardize and run k-means (k=3,4,5) with silhouette score for k selection.
  - Compare clusters to the administrative cerchie using adjusted Rand index.
- **Falsifiable output.** A cluster map (zone to cluster), silhouette curve, and adjusted-Rand-index table.

---

## Tier 2 | Useful but need a modest new input or modelling step

### 2.1 Causal identification of drug-crash link via interrupted time series

- **Question.** CrashDrugUse found no robust yearly correlation. Is there a credible causal design (rather than a correlation) that could test a specific drug-enforcement event?
- **Why it matters.** A null finding from correlation is weaker than a null finding from a properly-designed quasi-experiment.
- **Data needed.** A precise date of a Milan-relevant drug-enforcement policy change (e.g. a roadside drug-testing law amendment) + daily crashes around it. Domain input required.
- **Method.**
  - Interrupted time-series (ITS) with segmented regression:

    `crashes_t = a + b1 * t + b2 * I[t >= event] + b3 * t * I[t >= event] + season + trend + error`

  - Robust (Newey-West) SEs to handle serial correlation.
  - Placebo dates in the same month pre-event for specificity.
- **Falsifiable output.** ITS coefficient table with pre/post level and slope shifts, plus a placebo-date distribution for comparison.

### 2.2 Speed camera deployment effect (difference-in-differences)

- **Question.** Did the deployment of speed-enforcement cameras change per-km2 or per-crash severity in affected zones vs controls?
- **Why it matters.** Direct policy-impact question with a clean DiD structure.
- **Data needed.** Dates and locations of Milan speed camera deployments (Polizia Locale or Municipio publications). Zone-crash data we already have.
- **Method.**
  - Staggered DiD with Callaway-Sant'Anna estimator (or two-way fixed effects with event-time dummies).
  - Outcome: monthly crashes per km2 or fatal rate per crash in each Municipio.
  - Diagnostics: parallel-trends plot in event time, pre-treatment placebo tests.
- **Falsifiable output.** Event-time coefficient plot with 95% CI and an overall ATT estimate.

### 2.3 Hierarchical Bayesian severity model

- **Question.** Our current Poisson GLMs treat ring and month as fixed effects. What do partial-pooling estimates look like for low-count cells (e.g. deaths in Entro Navigli)?
- **Why it matters.** Low-count cells currently have wide CIs and sometimes implausible IRRs. Partial pooling would stabilize them.
- **Data needed.** Already on disk.
- **Method.**
  - Hierarchical Poisson in `brms` (R) or `pymc` / `numpyro` (Python): `Morti_{rt} ~ Poisson(Incidenti_{rt} * mu_{rt})` with `log(mu) = alpha_r + beta_m + epsilon_{rt}`, and `alpha_r ~ Normal(alpha_0, sigma_ring)`, `beta_m ~ Normal(beta_0, sigma_month)`.
  - Compare posterior means to the fixed-effect IRRs; check for shrinkage in small cells.
  - Posterior-predictive check on held-out months.
- **Falsifiable output.** Side-by-side coefficient table (fixed-effect IRR vs posterior mean IRR), and a shrinkage plot.

### 2.4 Gradient-boosted classifier for crash type with temporal CV

- **Question.** Our logit + RF baseline on crash type hits macro-F1 ~ 0.10 out-of-period. Can a properly-tuned XGBoost with weather, calendar, and zone features do better?
- **Why it matters.** The current notebook concludes "prediction is weak"; a stronger model would test whether that is a feature-set limitation or a fundamental ceiling.
- **Data needed.** The merged panel from 1.3 + weather from 1.6.
- **Method.**
  - `xgboost` with `objective=multi:softprob`, class-weight balancing via sample weights, and `n_estimators` chosen by early stopping on a blocked temporal CV (`sklearn`'s `TimeSeriesSplit`).
  - Report macro-F1, per-class ROC-AUC on the 2021+ holdout, and Platt-scaled calibration plots.
  - Feature importance via SHAP, interpreted as associational, not causal.
- **Falsifiable output.** Macro-F1 and per-class F1 table (baseline vs xgboost), SHAP summary plot, calibration plot on holdout.

### 2.5 Zone-level crash risk with small-area smoothing

- **Question.** At the Municipio level, which zones have *elevated* crash risk relative to their expected rate under a smooth spatial model?
- **Why it matters.** Zone-level actionable hotspots, not ring-level averages.
- **Data needed.** Already on disk + Municipio boundary shapefile (public, from Geoportale del Comune di Milano).
- **Method.**
  - Besag-York-Mollie (BYM) spatial Poisson model: `log(mu_i) = alpha + u_i + v_i` where `u` is CAR-spatial and `v` is exchangeable noise.
  - Rank zones by posterior `exceedance probability` `Pr(u_i + v_i > 0 | data)`.
  - Map the top decile.
- **Falsifiable output.** A Municipio map of exceedance probabilities with a top-10 table.

### 2.6 Granger-causality between fleet composition changes and crash rates

- **Question.** Fleet.ipynb shows that post-2020 the motorcycle-share / crash relationship weakens. Is there *any* directional lead-lag signal we are missing?
- **Why it matters.** A short-run lead-lag would salvage the fleet-as-predictor narrative that the robustness tests killed.
- **Data needed.** Already on disk.
- **Method.**
  - Vector autoregression with orders chosen by AIC/BIC on the short panel.
  - Granger-causality Wald tests on each direction.
  - Out-of-sample rolling 1-step-ahead forecast MAPE vs a univariate AR(1) baseline.
- **Falsifiable output.** VAR coefficient table, Granger chi2 with BH q-values, and a forecast accuracy comparison.

---

## Tier 3 | Exploratory or dependent on new external data

### 3.1 Socio-economic overlay (ISTAT census)

- **Question.** Do crashes per km2 scale with population density, income, or car ownership at the Municipio level?
- **Why it matters.** Separates geographic risk from socio-economic risk. A ring can be "dangerous" for structural-built-environment reasons or for socio-economic ones.
- **Data needed.** ISTAT census per Municipio (population, income, car ownership, employment), plus the shapefile.
- **Method.**
  - Cross-sectional multilevel regression at Municipio level with outcome `mean monthly crashes per km2` and predictors `density, income, age-group shares, car-ownership per 1000`.
  - Spatial lag or spatial error model diagnostic for residual autocorrelation.
- **Falsifiable output.** Coefficient table with CIs and Moran's I on residuals.

### 3.2 Network-based road infrastructure features

- **Question.** Are the ring-level severity differences explained by road-network characteristics (arterial density, intersection complexity, speed-limit mix)?
- **Why it matters.** Mechanistic explanation for the outer-ring severity premium.
- **Data needed.** OpenStreetMap extract for Milan + speed-limit data.
- **Method.**
  - Compute per-ring summary statistics: intersection density, arterial share, mean speed limit, share of signalized intersections.
  - Add to the Cerchie Poisson model and check whether the ring dummies absorb into these infrastructure controls.
- **Falsifiable output.** Before/after ring-IRR table (ring dummies only vs ring dummies + infra controls).

### 3.3 E-scooter / micro-mobility exposure

- **Question.** Did the arrival of e-scooter sharing in Milan (~2019) shift the crash-type distribution, severity, or pedestrian-crash rate?
- **Why it matters.** Directly tests a commonly-cited narrative about post-2018 mobility change.
- **Data needed.** AMAT Milan mobility reports or operator-trip-volume APIs.
- **Method.**
  - ITS on the share of pedestrian crashes around Q3 2019 launch, with placebo dates.
  - Regime-shift test (like Fleet.ipynb's `post2020` test) but anchored to the mobility-regime boundary, not the pandemic.
- **Falsifiable output.** ITS level-shift and slope-shift estimates on pedestrian crash share with BH q.

### 3.4 Under-reporting correction via capture-recapture

- **Question.** Non-fatal crashes are systematically under-reported. Can we estimate the under-reporting rate and correct the rings + CrashType analyses?
- **Why it matters.** All injury-rate and non-fatal-crash results are sensitive to reporting bias. A correction would strengthen every downstream claim.
- **Data needed.** An independent source of the same crash events (e.g. Pronto Soccorso hospital data, or insurance-claim data).
- **Method.**
  - Capture-recapture (Chapman estimator or log-linear model for K samples).
  - Refit all Poisson IRRs with the corrected totals and compare coefficients.
- **Falsifiable output.** Estimated under-reporting rate with CI, plus a before/after comparison of the main IRRs.

### 3.5 Calibration of the drug-crash null with external evidence

- **Question.** Our CrashDrugUse null is compatible with many priors (truly null, too-small-n, wrong-scale confound). Can we triangulate with external literature?
- **Why it matters.** A defensible "null" conclusion needs external support; otherwise it reads as "we did not find it".
- **Data needed.** Literature: meta-analyses of drug-impaired driving and crash rates in other EU cities.
- **Method.**
  - Bayesian meta-analytic prior built from the literature, combined with the Milan likelihood.
  - Report posterior mean and 95% credible interval on each effect; compare "posterior-consistent-with-zero" to "posterior-consistent-with-literature".
- **Falsifiable output.** A one-page table: Milan likelihood effect vs literature prior vs posterior, with a verdict column.

---

## Cross-cutting: quality-of-life improvements for the existing notebooks

These do not add findings but make the current results more trustworthy and easier to re-run.

- **Deterministic seeds in every notebook.** `np.random.seed(42)` is set in CrashType.ipynb but not all cells use it; propagate the same seed into every bootstrap/permutation call.
- **`.ipynb` output freshness guard.** Add a small `papermill` or `nbconvert --execute` job in CI that re-runs every notebook and fails if outputs drift. Currently outputs can silently go stale after data updates.
- **Shared inference helpers.** The permutation, partial-correlation, and bootstrap-CI helpers are re-implemented in multiple notebooks (CrashDrugUse, Fleet, CrashType). Move them into `scripts/inference_utils.py` and import.
- **Units on every table column.** `deaths_per_1000_inc`, `crashes_per_10k_fleet`, `per_km2` are self-documenting; `IRR`, `partial_r`, `q_value` are not. Add a one-line legend at the top of each computed table.
- **Pre-registration note.** For Tier 1 analyses, write down the tests we will run *before* running them (hypothesis, metric, rejection rule). This protects against after-the-fact HARKing and is cheap to do now.
