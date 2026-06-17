# Findings: Milan's Road Safety Story

This version is written for class presentation: each block gives a clear question, the main conclusion, a plausible mechanism, and the exact evidence.

## How to read this document

Every block below follows the same four-line structure so the argument is auditable.

- **Question** names the policy-relevant question the notebook answers.
- **Conclusion** states the defensible answer.
- **Hypothesis** proposes a plausible mechanism (never the evidence).
- **Finding** gives the exact statistical artefact (effect size, p or q, CI, n).

Key inferential vocabulary used throughout:

- **Incidence-rate ratio (IRR).** Poisson-GLM coefficient exponentiated. `IRR = 1` = same rate as the reference group; `IRR = 2` = double the rate, holding covariates fixed.
- **Offset `log(Incidenti)`** in a Poisson model converts the outcome to a per-crash rate (e.g. deaths per crash), so IRRs describe severity, not volume.
- **Partial correlation.** Correlation between `x` and `y` after regressing both on controls (typically `Year`, or trend + seasonal harmonics). Isolates short-run co-movement from shared drift.
- **First-difference correlation.** Correlation between `Δx_t` and `Δy_t`. Removes any constant level or trend; surviving pairs genuinely move together year-over-year.
- **Benjamini–Hochberg (BH) correction.** Converts a family of p-values into q-values controlling the false-discovery rate at the stated threshold (usually 5%).
- **Robust evidence.** Our strictest label: the pair passes BH on the partial correlation **and** is significant under first-differencing **and** (for CrashType) has `|ρ_partial| ≥ 0.2`.

## Cerchie.ipynb | The Geography of Risk

- Question: If we map Milan by rings and normalize by area, where is crash pressure highest, and does that match where crashes are most severe?
- Conclusion: The most dangerous ring for crash concentration is Dalle Mura Spagnole alla Nuova Circonvallazione (12.198 incidents/km2), which is about 3.44x the outer ring burden (3.542 incidents/km2). This same ring is also first for fatalities per km2 (0.0417), so it is the clearest priority zone for near-term safety action because it combines both high event density and high human harm.
- Hypothesis: Ring-level differences in road geometry, speed profile, and user mix (cars, motorcycles, bicycles, pedestrians) create distinct risk signatures.
- Finding: Total incidents per km2 rank as Dalle Mura Spagnole alla Nuova Circonvallazione (12.1980) > Entro la Cerchia dei Navigli (8.9062) > Dalla Cerchia dei Navigli alle Mura Spagnole (8.4774) > Dalla Nuova Circonvallazione ai confini del Comune (3.5419). Fatalities per km2 rank as Dalle Mura Spagnole alla Nuova Circonvallazione (0.0417) > Dalla Cerchia dei Navigli alle Mura Spagnole (0.0264) > Dalla Nuova Circonvallazione ai confini del Comune (0.0207) > Entro la Cerchia dei Navigli (0.0129).

- Question: Are ring-level severity differences (deaths per crash, not deaths per km2) statistically real, or just visual noise?
- Conclusion: These differences are not visual noise: they remain strongly significant after exposure and season controls (Morti chi2 = 85.929, p = 1.64e-18; Feriti chi2 = 568.672, p = 6.23e-123). Per-crash severity is especially elevated in the outer ring (Morti IRR = 4.025 vs Entro), which means fewer total crashes there can still translate into disproportionately severe outcomes.
- Hypothesis: Structural characteristics of each ring (intersection density, arterial corridors, and operating speeds) generate persistent severity gaps that show up only once we neutralize exposure with a crash-count offset.
- Finding: Poisson models with `log(Incidenti)` offset and month fixed effects, reference ring re-expressed as Entro la Cerchia dei Navigli, show a strong ring effect: Morti chi2 = 85.929 (df = 3, p = 1.64e-18) and Feriti chi2 = 568.672 (df = 3, p = 6.23e-123). Morti IRRs are 2.163 (Navigli-Mura), 2.363 (Mura-Nuova), and 4.025 (outer ring), all BH-significant. Non-parametric bootstrap 95% CIs for deaths per 1,000 crashes are: Entro [0.66, 2.32], Navigli-Mura [2.27, 3.97], Mura-Nuova [3.00, 3.86], outer [5.44, 6.25] - these non-overlapping CIs confirm the IRR conclusion independently.

- Question: Should Milan treat month-of-year risk as random or structural?
- Conclusion: Month-of-year risk is structural, not random, in every ring. The strength of seasonality spans from already-strong Entro (chi2 = 303.08) to extremely concentrated outer-ring dynamics (chi2 = 3937.54), so Milan should schedule prevention with a ring-specific calendar rather than a single citywide timing.
- Hypothesis: Travel demand cycles (weather, school calendar, holidays, tourism) shift exposure and conflict patterns month by month, and the amplitude of those cycles differs sharply across the city.
- Finding: Chi-square month-uniformity tests (df = 11) are highly significant for incidents in all rings: chi2 = 303.08 (Entro), 750.23 (Navigli-Mura), 2520.75 (Mura-Nuova), 3937.54 (outer ring), all with p << 0.001 after BH.

## CerchieSeasonality.ipynb | The Calendar of Risk

- Question: Do Milan's rings share the same seasonal crash pattern, or does each ring have its own calendar of risk?
- Conclusion: The rings share the same descriptive peak-trough timing (October peak, August trough), but they do not share the same seasonal intensity. The strongest result is amplitude, not a clean phase shift: the outer ring has the largest absolute swing (309.4 crashes from trough to peak), while Dalla Cerchia dei Navigli alle Mura Spagnole has the largest peak/trough ratio (3.22x). Prevention should therefore be ring-specific in timing and scale, not only a single citywide seasonal campaign.
- Hypothesis: Seasonal exposure cycles such as school calendars, commuting rhythms, holidays, tourism, and weather-sensitive travel alter traffic conflicts month by month, and those exposure shifts have different intensity across rings.
- Finding: In a Poisson GLM for monthly crash counts with `log(area_km2)` offset, year fixed effects, annual and semi-annual harmonics, and ring x harmonic interactions, the global likelihood-ratio test rejects equal seasonal shape across rings (LR = 155.22, df = 12, p = 4.93e-27). Because overdispersion is high (Pearson dispersion = 7.43), conservative harmonic checks are weaker and borderline (HC0 robust Wald p = 0.055; negative-binomial LRT p = 0.058), but the flexible month fixed-effects robustness model still strongly rejects equal ring calendars (`C(Cerchia):C(month)` LR = 281.84, df = 33, p = 2.78e-41). Descriptive peak months are October for all four rings and trough months are August for all four rings. Mean monthly crash swings are: outer ring 309.4 (ratio 1.94x), Mura-Nuova 185.8 (2.35x), Navigli-Mura 48.9 (3.22x), Entro 22.3 (2.81x). Harmonic annual peak estimates are less stable (Entro November, Navigli-Mura January, Mura-Nuova July, outer July), so the presentation-safe claim is ring-specific amplitude in crash counts, not proven ring-specific crash severity or weather causation.

## CrashDrugUse.ipynb | Signal Versus Mirage

- Question: Do yearly wastewater drug signals track yearly crash outcomes in Milan?
- Conclusion: At raw yearly level, the signal is narrow and one-directional: only cocaine and cannabis are significant, all links are inverse, and none involve fatal crashes. The strongest links (around r = -0.72 to -0.76) are therefore better interpreted as a pattern worth scrutiny, not as evidence that higher drug markers reduce crash risk.
- Hypothesis: Shared long-run trends (mobility shifts, enforcement changes, reporting differences) can generate strong correlations even without direct causal linkage, especially on short yearly panels (n = 10 to 14).
- Finding: Significant raw yearly pairs are non_fatal_crashes vs cocaine (r = -0.717, n = 14, p = 0.0014), total_crashes vs cocaine (r = -0.716, n = 14, p = 0.0022), non_fatal_crashes vs cannabis (r = -0.764, n = 10, p = 0.0076), total_crashes vs cannabis (r = -0.763, n = 10, p = 0.0082). All permutation-based.

- Question: Do those links survive strict robustness checks?
- Conclusion: No. Once we apply trend control, lag checks, first-difference logic, and BH correction, the evidence drops to zero fully robust pairs (from 4 BH-significant raw pairs and 2 BH-significant partial pairs), so no metabolite can be defended as a stable predictor of Milan crash dynamics in this panel.
- Hypothesis: Most of the apparent effect is trend-coupling: both crash counts and per-capita metabolite loads drift over the decade for separate reasons, which mechanically inflates Pearson r on raw levels.
- Finding: Across 15 eligible pairs, BH-significant counts are raw q < 0.05: 4, year-controlled partial q < 0.05: 2, lag q < 0.05: 0, and robust_signal (q_partial < 0.05 plus first-difference significance) = 0. The strongest raw pair (non_fatal_crashes vs cocaine) remains sign-stable under leave-one-year-out (consistency = 1.000) but still fails the full robustness criterion.

## Fleet.ipynb | The Fleet Narrative, Corrected

- Question: Are fleet-crash relationships robust after removing trend artifacts and controlling false discoveries?
- Conclusion: Mostly no, and the collapse is decisive: 37 BH-significant raw pairs fall to 0 trend-adjusted significant pairs, 0 first-difference significant pairs, and 0 robust pairs. This indicates that most fleet-crash correlations are dominated by shared long-term trajectories rather than stable causal structure.
- Hypothesis: Fleet variables and crashes share broad multi-year trajectories (e.g. post-2008 contraction, urban mode shift), which can mechanically inflate naive associations.
- Finding: BH-significant pair counts are raw: 37, year-controlled partial: 0, first-difference: 0, robust_evidence pairs: 0. Pearson and Spearman permutation p-values agree.

- Question: Did the relationship between fleet composition and crashes change after 2020?
- Conclusion: Yes, there is strong regime-shift evidence: the motorcycle_share:post2020 interaction is significant (coef = 486461.95, p = 0.0027), while rolling correlation weakens materially from about -0.99 to -0.60. In presentation terms, the relationship changed era, so pre-2020 coefficients should not be treated as portable to the post-2020 period.
- Hypothesis: Pandemic and post-pandemic mobility regimes changed exposure composition and risk pathways (more bicycles, shifted commute peaks, new micro-mobility).
- Finding: In `total_crashes ~ Year + motorcycle_share + post2020 + motorcycle_share:post2020`, the interaction term is positive and significant (coef = 486461.95, p = 0.0027, HC3). Rolling 8-year correlation between motorcycle_share and total_crashes remains negative but weakens from about -0.99 to about -0.60.

- Question: What is the most policy-relevant fleet finding that remains stable?
- Conclusion: The most policy-relevant and stable message is long-run safety improvement per exposure unit: all key slopes are significantly negative (for total crashes, crashes per 10k fleet, fatal crashes per 100k fleet, and deaths per 100k fleet). This is stronger and more decision-useful than any isolated composition correlation because it captures system-level progress sustained over years.
- Hypothesis: Safety technology, infrastructure improvements, and behavior adaptation have outpaced risk pressure from fleet growth and composition changes.
- Finding: Exposure-adjusted trends are all negative and significant: total_crashes = -538.2298/year, crashes_per_10k_fleet = -5.5397/year, fatal_crashes_per_100k_fleet = -0.2817/year, deaths_per_100k_fleet = -0.2988/year (all permutation p = 0.0001, bootstrap 95% CIs below zero).

## CrashType.ipynb | Structure Yes, Prediction No

- Question: Which contextual variables are genuinely associated with the share of each crash type, once trend and seasonality are removed?
- Conclusion: 14 crash-type-by-context pairs survive the full robustness standard (BH on partial Spearman + first-difference significance + |rho| >= 0.2). The clearest signal is structural: 2-vehicle share is strongly linked with Scontro frontale-laterale (partial rho = 0.600) while 1-vehicle share moves in the opposite direction. Pedestrian crashes (Investimento pedone) track 1-vehicle share upward (partial rho = 0.549), consistent with the definitional fact that pedestrian strikes are typically single-vehicle events.
- Hypothesis: Crash type is partly a mechanical signature of the vehicle configuration on scene: lone-vehicle months coincide with run-off and pedestrian events, multi-vehicle months coincide with lateral-frontal collisions.
- Finding: Top robust partial Spearman correlations (n = 285 monthly observations per pair, all with `stable_sign = True`, all BH q << 0.001): Scontro frontale-laterale vs share_2v (rho = 0.600, q = 2.2e-27); Scontro frontale-laterale vs share_1v (rho = -0.578, q = 3.3e-25); Investimento pedone vs share_1v (rho = 0.549, q = 1.7e-22); Investimento pedone vs share_2v (rho = -0.539, q = 1.4e-21); Urto con ostacolo vs share_1v (rho = 0.420, q = 1.5e-12). Five crash types enter the robust set on vehicle-mix alone.

- Question: Which crash types are genuinely more severe per crash, once exposure is neutralized?
- Conclusion: Adjusted for crash volume via a Poisson offset, pedestrian crashes are dramatically deadlier than any other category and frontal-head-on collisions are a distant second, while several categories have injury-per-crash rates above baseline but with much smaller multipliers. This per-crash severity view is the one that should drive vulnerable-road-user policy, not raw counts.
- Hypothesis: Pedestrian and head-on crash kinematics concentrate energy on unprotected road users (pedestrians) or directly oppose two vehicles at near-combined-speed, so conditional on occurrence they are disproportionately fatal.
- Finding: Poisson GLMs with `log(Incidenti)` offset, HC3 standard errors, and `C(month) + year` controls (so IRRs net out seasonality and era), referenced to "Altre cause". Highest death-rate IRR: Investimento pedone IRR = 7.56, 95% CI [3.93, 14.53], q = 1.02e-08. Highest injury-rate IRR: Tamponamento IRR = 1.38, CI [1.36, 1.40], q ~ 0; Scontro frontale IRR = 1.36, CI [1.32, 1.39], q = 3.1e-135; Scontro frontale-laterale IRR = 1.32, CI [1.31, 1.34], q ~ 0.

- Question: Can a crash-type model trained on earlier years reliably classify later years?
- Conclusion: Out-of-period generalization is weak and operationally limited (temporal-holdout accuracy 0.17, macro F1 0.10), with several classes showing near-zero recall. The model can support descriptive insight about structure (see the two findings above) but it is not reliable enough for forecasting or resource allocation by predicted crash type.
- Hypothesis: Crash-type composition evolves over time (shifting mix of pedestrian events, new micro-mobility exposure, post-2020 mobility regime), and the available predictors do not fully capture the regime shifts, so features learned pre-2020 do not transfer.
- Finding: Temporal holdout with train years <= 2020 and test years > 2020 yields accuracy = 0.17, macro F1 = 0.10, weighted F1 = 0.10. Several classes show zero precision and zero recall on the holdout (Scontro frontale, Scontro frontale-laterale, Urto con ostacolo, Urto con veicolo in fermata o sosta), with predictions concentrated in a smaller subset of classes. Random-CV accuracy (0.17, macro F1 0.10) and the temporal-holdout accuracy coincide here, so the weakness is not simply a time-split artefact: it is structural to the current feature set.

## Presentation Close | What Milan Teaches Us

- Question: What is the clearest city-level story we can present with confidence?
- Conclusion: The defensible city story has three pillars. (1) *Where*: Dalle Mura Spagnole alla Nuova Circonvallazione is the top crash-pressure ring and the outer ring is the top per-crash-severity ring, a distinction that matters for policy targeting. (2) *When*: ring seasonality is structurally significant everywhere, and the new seasonality model shows the clearest difference is amplitude rather than a clean phase shift, so prevention should be ring-specific in timing and scale. (3) *What*: crash type is structurally tied to vehicle-mix and to per-crash severity (pedestrian IRR ~ 7), even though crash type is not predictable out-of-period. At the same time, drug and aggregate fleet annual correlations largely fail robustness, so Milan's strongest evidence supports place-based, time-targeted, and type-aware safety policy rather than single-factor causal narratives.
- Hypothesis: Urban safety in Milan is shaped by interacting systems (space, season, mobility regime, vehicle configuration, and road-user mix) rather than a single dominant annual factor.
- Finding: Ring-level effects are statistically strong; seasonality is significant across rings; the ring x seasonality model rejects equal seasonal shape by Poisson LRT (p = 4.93e-27) and flexible month fixed effects (p = 2.78e-41), while conservative harmonic overdispersion checks are borderline (robust Wald p = 0.055; negative-binomial p = 0.058); fleet risk per exposure declines over time; crash-type x vehicle-mix partial correlations survive full robustness; pedestrian-crash IRR is an order of magnitude above baseline. CrashDrugUse and the raw CrashType classifier both caution against overclaiming predictive or causal power from raw associations.

## Limitations and Scope

These bound how far the above findings should be extrapolated.

- **Exposure proxies.** Per-km2 normalization measures geographic pressure, not personal risk. We do not have vehicle-kilometres-travelled (VKT) or minutes-walked data, so "safest ring" statements are always per-area or per-crash, never per-trip.
- **Sample size on annual panels.** CrashDrugUse (n = 10 to 14) and Fleet (n ~ 15 to 19) are short time series. Even permutation-based tests cannot fully compensate for small n when long-run trends dominate; the robust-evidence thresholds are appropriately conservative.
- **Reference-class dependence.** IRRs depend on the reference group (CrashType uses "Altre cause"; Cerchie re-expresses to Entro la Cerchia dei Navigli). Rankings are reference-invariant, but specific IRR values are not.
- **Observational design.** Every statistic here is observational. Survival of the robustness battery is necessary but not sufficient for causal claims; unmeasured confounders (enforcement intensity, infrastructure investments, under-reporting shifts) remain.
- **Area approximations.** Two of the four ring areas are approximations (21.33 and 150.84 km2). Per-km2 rankings within +/-10% of a tied pair should be read cautiously; the Mura-Nuova lead over Entro on total/km2 is well outside that band, so the ranking is not sensitive to area uncertainty.
- **Class imbalance in CrashType.** The target distribution is heavy-tailed; macro-F1 is the right metric but even a well-calibrated model inherits the imbalance. The temporal-holdout numbers should be read as a ceiling on current-feature-set performance, not on crash-type modelling in principle.

## Area C Exposure Check

- Question: Does Area C exposure change how we read central-ring crash counts?
- Conclusion: Yes, but only for the rings inside the Mura Spagnole. After merging Area C monthly accesses as a central-area exposure proxy, Dalla Cerchia dei Navigli alle Mura Spagnole still has a higher crash burden than Entro la Cerchia dei Navigli: 1.27 versus 0.64 mean monthly crashes per 100,000 Area C accesses.
- Hypothesis: Even after accounting for vehicles entering Area C, the Navigli-to-Mura-Spagnole ring has more conflict points or higher residual street risk than the innermost ring.
- Finding: `milan_crashes_city_ring_area_c_exposure.csv` contains 306 central-ring rows with Area C exposure from 2012-01 to 2024-11. Mean monthly incidents per 100,000 Area C accesses are 1.272 for Dalla Cerchia dei Navigli alle Mura Spagnole and 0.640 for Entro la Cerchia dei Navigli. Area C is not used as an exposure denominator for outer rings or citywide notebooks.
