# Findings

## Cerchie.ipynb

- Q: What is the normalized danger ranking by cerchia for total crashes?
- Finding: Highest to lowest (total incidents per km2): Dalle Mura Spagnole alla Nuova Circonvallazione (12.1980) > Entro la Cerchia dei Navigli (8.9062) > Dalla Cerchia dei Navigli alle Mura Spagnole (8.4774) > Dalla Nuova Circonvallazione ai confini del Comune (3.5419).
- Conclusion: The middle ring (Dalle Mura Spagnole alla Nuova Circonvallazione) is the main hotspot for crash frequency per area, so prevention focused on high-volume urban interactions should be prioritized there.
- Hypothesis: This ring likely concentrates dense mixed traffic (cars, scooters, bikes, pedestrians), commercial activity, and many intersections, increasing total crash opportunities.

- Q: What is the normalized danger ranking by cerchia for fatalities (Morti)?
- Finding: Highest to lowest (fatalities per km2): Dalle Mura Spagnole alla Nuova Circonvallazione (0.0417) > Dalla Cerchia dei Navigli alle Mura Spagnole (0.0264) > Dalla Nuova Circonvallazione ai confini del Comune (0.0207) > Entro la Cerchia dei Navigli (0.0129).
- Conclusion: The fatality risk pattern is not identical to total crashes, so where crashes happen most and where crashes are deadliest should be treated as related but different risk maps.
- Hypothesis: Dalla Cerchia dei Navigli alle Mura Spagnole may have fewer crashes than Entro, but relatively more severe outcomes per crash due to speed profile, night mobility, or different road geometry.

- Q: What is the normalized ranking for the non-fatal proxy (Feriti)?
- Finding: Highest to lowest (Feriti per km2): Dalle Mura Spagnole alla Nuova Circonvallazione (15.9437) > Dalla Cerchia dei Navigli alle Mura Spagnole (10.7318) > Entro la Cerchia dei Navigli (10.4915) > Dalla Nuova Circonvallazione ai confini del Comune (4.7564).
- Conclusion: Injury burden per area is concentrated in the two inner-middle rings, suggesting that reducing injury severity there could materially lower total harm even if crash counts stay similar.
- Hypothesis: Higher exposure of vulnerable users (two-wheelers and pedestrians) and conflict-heavy junctions in these rings may increase injuries per crash.

- Q: Why can total-incident ranking differ from fatalities/Feriti ranking?
- Finding: Incidenti counts crashes, while Morti and Feriti count people involved. Entro la Cerchia dei Navigli has slightly more crashes per km2 than Dalla Cerchia dei Navigli alle Mura Spagnole (8.9062 vs 8.4774), but lower severity per crash (Feriti per incidente: 1.1780 vs 1.2659; Morti per 1000 incidenti: 1.4439 vs 3.1177).
- Conclusion: Severity-adjusted indicators are essential; relying only on crash counts can hide where collisions are more harmful.
- Hypothesis: Differences in impact speed, road type mix, and time-of-day patterns may drive this divergence in per-crash severity.

- Q: Which months are highest and lowest risk in the normalized monthly profiles?
- Finding: For citywide resolved total crashes per km2, October is highest (6.1852) and August is lowest (2.8968). For fatalities (Morti) per km2, October is highest (0.0365) and July is lowest (0.0152). Fatality intensity relative to normalized crashes is highest in August (5.4967 per 1000).
- Conclusion: Seasonality differs by metric: late autumn has the highest overall burden, while summer has fewer crashes but not proportionally fewer deadly outcomes.
- Hypothesis: August likely has lower traffic volume (fewer crashes) but a higher severity mix, possibly related to higher average speed on emptier roads, alcohol/night-driving exposure, tourism travel, or heat/fatigue effects.

## CrashDrugUse.ipynb

- Q: Which crash-drug yearly correlations are statistically relevant for Milan?
- Method: Pearson correlation on yearly merged data (2011-2024, min shared years n>=5), with two-sided permutation p-values (5,000 shuffles) and relevance threshold p<0.05.
- Finding: Statistically relevant pairs are all negative and involve non-fatal or total crashes.
- Significant pair: non_fatal_crashes vs cocaine (r=-0.717, n=14, p=0.0014).
- Significant pair: total_crashes vs cocaine (r=-0.716, n=14, p=0.0022).
- Significant pair: non_fatal_crashes vs cannabis (r=-0.764, n=10, p=0.0076).
- Significant pair: total_crashes vs cannabis (r=-0.763, n=10, p=0.0082).
- Conclusion: In the available yearly overlap, higher measured cocaine/cannabis wastewater levels are associated with lower non-fatal and total crash counts; fatal-crash links are not statistically relevant under this threshold.
- Hypothesis: The inverse association may reflect confounding trends (post-2010 urban mobility changes, enforcement, reporting dynamics, exposure shifts) rather than a direct protective effect; this should be treated as correlation-only evidence.

## Fleet.ipynb

- Q: Are Milan fleet levels and composition statistically associated with crash burden when trend effects are accounted for?
- Method: Yearly merge of `milan_vehicle_fleet_cleaned.csv` with yearly crash totals aggregated from `milan_crashes_monthly_cleaned.csv` (2004-2022 overlap, n=18, missing 2009). Inference uses two-sided permutation p-values for Pearson/Spearman correlations, year-controlled partial correlations, annualized first-difference checks, and year-slope tests with bootstrap confidence intervals.

- Finding: Raw yearly correlations for total crashes are strong and opposite by fleet composition: fleet_cars (r=0.943, p=0.0001), fleet_motorcycles (r=-0.958, p=0.0001), fleet_heavy_goods (r=0.638, p=0.0042), while fleet_total is weaker (r=0.410, p=0.0897).
- Conclusion: Raw associations are not sufficient for interpretation because several variables share strong long-run time trends.
- Hypothesis: Opposite secular trajectories (declining cars, rising motorcycles, declining crashes) mechanically inflate naive correlations.

- Finding: After controlling for year, total crashes remain associated with fleet_total (partial r=0.563, p=0.0165), fleet_heavy_goods (partial r=0.574, p=0.0129), and motorcycle_share (partial r=-0.509, p=0.0306), while fleet_cars is borderline/non-significant (partial r=0.447, p=0.0638).
- Conclusion: Part of the fleet-crash relationship survives simple linear trend control, but effect strength depends on variable choice and should be treated as associative, not causal.
- Hypothesis: Fleet structure shifts and broader mobility/system changes likely move together with crashes, creating residual associations even after linear detrending.

- Finding: In annualized first differences (n=17), no fleet-crash pair reaches p<0.05; strongest are d_deaths vs d_fleet_heavy_goods (r=0.401, p=0.1157) and d_fatal_crashes vs d_fleet_heavy_goods (r=0.398, p=0.1175).
- Conclusion: Short-run year-to-year co-movement evidence is weak, reducing support for immediate direct coupling between annual fleet changes and annual crash changes.
- Hypothesis: Yearly crash fluctuations may be driven more by policy, exposure conditions, enforcement, and exogenous shocks than by same-year fleet deltas alone.

- Finding: Exposure-adjusted crash risk declines strongly over time: total_crashes slope=-538.2298/year (p=0.0001; 95% CI [-634.7469, -447.9961]); crashes_per_10k_fleet slope=-5.5397/year (p=0.0001; 95% CI [-6.4867, -4.6522]); fatal_crashes_per_100k_fleet slope=-0.2817/year (p=0.0001; 95% CI [-0.3572, -0.2003]); deaths_per_100k_fleet slope=-0.2988/year (p=0.0001; 95% CI [-0.3771, -0.2117]).
- Conclusion: The statistically strongest fleet-linked result is not a positive fleet-growth risk effect, but a sustained decline in crash burden per unit of registered fleet.
- Hypothesis: Safety technology improvements, infrastructure changes, enforcement, and behavior adaptation likely outpaced risk from fleet expansion/composition changes over this period.

- Finding: Sensitivity checks show instability across subperiods. For total crashes and motorcycle_share, pre-covid is strong (partial r=-0.7076, p=0.0034) but post-2010 is null (partial r=-0.0041, p=0.9873); fleet_heavy_goods remains significant post-2010 (partial r=0.5806, p=0.0339).
- Conclusion: Subperiod instability suggests structural breaks and cautions against a single stationary fleet-crash relationship for 2004-2022.
- Hypothesis: Pandemic-era and late-2010 mobility regime changes likely altered the relationship between fleet composition and crash outcomes.
