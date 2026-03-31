# Findings: Milan's Road Safety Story

This version is written for class presentation: each block gives a clear question, the main conclusion, a plausible mechanism, and the exact evidence.

## Cerchie.ipynb | The Geography of Risk

- Question: If we map Milan by rings and normalize by area, where is crash pressure highest, and does that match where crashes are most severe?
- Conclusion: The most dangerous ring for crash concentration is Dalle Mura Spagnole alla Nuova Circonvallazione (12.198 incidents/km2), which is about 3.44x the outer ring burden (3.542 incidents/km2). This same ring is also first for fatalities per km2 (0.0417), so it is the clearest priority zone for near-term safety action because it combines both high event density and high human harm.
- Hypothesis: Ring-level differences in road geometry, speed profile, and user mix (cars, motorcycles, bicycles, pedestrians) create distinct risk signatures.
- Finding: Total incidents per km2 rank as Dalle Mura Spagnole alla Nuova Circonvallazione (12.1980) > Entro la Cerchia dei Navigli (8.9062) > Dalla Cerchia dei Navigli alle Mura Spagnole (8.4774) > Dalla Nuova Circonvallazione ai confini del Comune (3.5419). Fatalities per km2 rank as Dalle Mura Spagnole alla Nuova Circonvallazione (0.0417) > Dalla Cerchia dei Navigli alle Mura Spagnole (0.0264) > Dalla Nuova Circonvallazione ai confini del Comune (0.0207) > Entro la Cerchia dei Navigli (0.0129).

- Question: Are these ring-level severity differences statistically real, or just visual noise?
- Conclusion: These differences are not visual noise: they remain strongly significant after exposure and season controls (Morti chi2 = 99.943, p = 1.60e-21; Feriti chi2 = 223.968, p = 2.79e-48). Severity intensity is especially elevated in the outer ring (Morti IRR = 4.025 vs Entro), which means fewer total crashes there can still translate into disproportionately severe outcomes.
- Hypothesis: Structural characteristics of each ring (intersection density, arterial corridors, and operating speeds) generate persistent severity gaps.
- Finding: Poisson models with log(Incidenti) offset and month fixed effects show a strong ring effect: Morti chi2 = 99.943 (df = 3, p = 1.60e-21) and Feriti chi2 = 223.968 (df = 3, p = 2.79e-48). Versus Entro la Cerchia dei Navigli, Morti IRRs are 2.163 (Navigli-Mura), 2.363 (Mura-Nuova), and 4.025 (outer ring), all significant.

- Question: Should Milan treat month-of-year risk as random or structural?
- Conclusion: Month-of-year risk is structural, not random, in every ring. The strength of seasonality spans from already-strong Entro (chi2 = 303.08) to extremely concentrated outer-ring dynamics (chi2 = 3937.54), so Milan should schedule prevention with a ring-specific calendar rather than a single citywide timing.
- Hypothesis: Travel demand cycles (weather, school calendar, holidays, tourism) shift exposure and conflict patterns month by month.
- Finding: Chi-square month-uniformity tests are highly significant for incidents in all rings: chi2 = 303.08 (Entro), 750.23 (Navigli-Mura), 2520.75 (Mura-Nuova), 3937.54 (outer ring), all with p << 0.001.

## CrashDrugUse.ipynb | Signal Versus Mirage

- Question: Do yearly wastewater drug signals track yearly crash outcomes in Milan?
- Conclusion: At raw yearly level, the signal is narrow and one-directional: only cocaine and cannabis are significant, all links are inverse, and none involve fatal crashes. The strongest links (around r = -0.72 to -0.76) are therefore better interpreted as a pattern worth scrutiny, not as evidence that higher drug markers reduce crash risk.
- Hypothesis: Shared long-run trends (mobility shifts, enforcement changes, reporting differences) can generate strong correlations even without direct causal linkage.
- Finding: Significant raw yearly pairs are non_fatal_crashes vs cocaine (r = -0.717, n = 14, p = 0.0014), total_crashes vs cocaine (r = -0.716, n = 14, p = 0.0022), non_fatal_crashes vs cannabis (r = -0.764, n = 10, p = 0.0076), total_crashes vs cannabis (r = -0.763, n = 10, p = 0.0082).

- Question: Do those links survive strict robustness checks?
- Conclusion: No. Once we apply trend control, lag checks, first-difference logic, and BH correction, the evidence drops to zero fully robust pairs (from 4 BH-significant raw pairs and 2 BH-significant partial pairs), so no metabolite can be defended as a stable predictor of Milan crash dynamics in this panel.
- Hypothesis: Most of the apparent effect is trend-coupling, not short-run co-movement.
- Finding: Across 15 eligible pairs, BH-significant counts are raw q < 0.05: 4, year-controlled partial q < 0.05: 2, lag q < 0.05: 0, and robust_signal (q_partial < 0.05 plus first-difference significance) = 0. The strongest raw pair (non_fatal_crashes vs cocaine) remains sign-stable under leave-one-year-out (consistency = 1.000) but still fails the full robustness criterion.

## Fleet.ipynb | The Fleet Narrative, Corrected

- Question: Are fleet-crash relationships robust after removing trend artifacts and controlling false discoveries?
- Conclusion: Mostly no, and the collapse is decisive: 37 BH-significant raw pairs fall to 0 trend-adjusted significant pairs, 0 first-difference significant pairs, and 0 robust pairs. This indicates that most fleet-crash correlations are dominated by shared long-term trajectories rather than stable causal structure.
- Hypothesis: Fleet variables and crashes share broad multi-year trajectories, which can mechanically inflate naive associations.
- Finding: BH-significant pair counts are raw: 37, year-controlled partial: 0, first-difference: 0, robust_evidence pairs: 0.

- Question: Did the relationship between fleet composition and crashes change after 2020?
- Conclusion: Yes, there is strong regime-shift evidence: the motorcycle_share:post2020 interaction is significant (coef = 486461.95, p = 0.0027), while rolling correlation weakens materially from about -0.99 to -0.60. In presentation terms, the relationship changed era, so pre-2020 coefficients should not be treated as portable to the post-2020 period.
- Hypothesis: Pandemic and post-pandemic mobility regimes changed exposure composition and risk pathways.
- Finding: In total_crashes ~ Year + motorcycle_share + post2020 + motorcycle_share:post2020, the interaction term is positive and significant (coef = 486461.95, p = 0.0027). Rolling 8-year correlation between motorcycle_share and total_crashes remains negative but weakens from about -0.99 to about -0.60.

- Question: What is the most policy-relevant fleet finding that remains stable?
- Conclusion: The most policy-relevant and stable message is long-run safety improvement per exposure unit: all key slopes are significantly negative (for total crashes, crashes per 10k fleet, fatal crashes per 100k fleet, and deaths per 100k fleet). This is stronger and more decision-useful than any isolated composition correlation because it captures system-level progress sustained over years.
- Hypothesis: Safety technology, infrastructure improvements, and behavior adaptation have outpaced risk pressure from fleet growth and composition changes.
- Finding: Exposure-adjusted trends are all negative and significant: total_crashes = -538.2298/year, crashes_per_10k_fleet = -5.5397/year, fatal_crashes_per_100k_fleet = -0.2817/year, deaths_per_100k_fleet = -0.2988/year (all p = 0.0001, bootstrap CIs below zero).

## CrashType.ipynb | Predicting Tomorrow from Yesterday

- Question: Can a crash-type model trained on earlier years reliably classify later years?
- Conclusion: Out-of-period generalization is weak and operationally limited (accuracy 0.17, macro F1 0.10), with several classes showing near-zero recall. The model can still support descriptive insight about structure, but it is not reliable enough for forecasting or resource allocation by predicted crash type.
- Hypothesis: Crash-type composition evolves over time and available predictors do not fully capture the regime shifts.
- Finding: Temporal holdout with train years <= 2020 and test years > 2020 yields accuracy = 0.17, macro F1 = 0.10, weighted F1 = 0.10. Several classes show near-zero recall (including Scontro frontale, Scontro frontale-laterale, Urto con ostacolo, and Urto con veicolo in fermata o sosta), with predictions concentrated in a smaller subset of classes.

## Presentation Close | What Milan Teaches Us

- Question: What is the clearest city-level story we can present with confidence?
- Conclusion: The defensible city story is precise: Dalle Mura Spagnole alla Nuova Circonvallazione is the top crash-pressure ring, ring seasonality is structurally significant everywhere, and exposure-adjusted safety trends improve despite temporal regime changes. At the same time, drug and fleet annual correlations largely fail robustness, so Milan's strongest evidence supports place-based and time-targeted safety policy rather than single-factor causal narratives.
- Hypothesis: Urban safety in Milan is shaped by interacting systems (space, season, mobility regime, and infrastructure) rather than a single dominant annual factor.
- Finding: Ring-level effects are statistically strong, seasonality is significant across rings, fleet risk per exposure declines over time, and both CrashDrugUse and CrashType results caution against overclaiming predictive or causal power from raw associations.

