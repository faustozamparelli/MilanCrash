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
