## Goal of the project
- Build a **high-grade Applied Statistics project** on road crashes, starting from **Milan crash reports** and then extending to other major Italian cities.
- Focus on **smart, well-posed research questions** and choose methods **because they fit the question and the data**, not just to show many techniques.
- Keep the project presentation-oriented: every step must produce something that can later become a slide, a figure, a table, or a defendable methodological choice.

## Core grading strategy
- Prioritize **clarity of presentation**, **relevance of the research question**, and **appropriateness of methods**.
- Prefer a project that is **coherent, interpretable, and statistically justified** over one that is technically flashy but fragmented.
- Prepare every choice so that each team member can explain: the problem setting, why the method was chosen, what the result means, and what the limitations are.

## Non-negotiable project structure

### Phase 0 - Ready state (already done)
- [x] Milan raw datasets downloaded and stored in `data/raw/`.
- [x] Base working folders are in place:
  - [x] `data/raw/`
  - [x] `data/processed/`
  - [x] `notebooks/`
  - [x] `scripts/`
- [x] Frozen raw-data snapshot saved for reproducibility.
- [x] Primary scope confirmed: **Milan first, then optional extension to major Italian cities**.
- [ ] Optional later (only when needed): `figures/`, `slides/`, `report_notes/`.

### Phase 1 - Start analysis now
- [ ] Build `data_dictionary.md` from the already downloaded Milan files:
  - [ ] variable name and meaning
  - [ ] type / unit
  - [ ] missingness notes
  - [ ] usable vs not usable for analysis
- [ ] Define the modeling target now:
  - [ ] severity variable to use
  - [ ] severe vs non-severe encoding rule
  - [ ] first predictor shortlist
- [ ] Start the first analysis pass in `notebooks/Milan_EDA.ipynb`:
  - [ ] dataset profile (rows, years, variable coverage)
  - [ ] missingness and data-quality scan
  - [ ] temporal severity patterns (hour, weekday, month)
  - [ ] spatial severity patterns (zone/district)
  - [ ] first 5-10 plain-language findings

### Phase 2 - Research questions (lock quickly, do not block progress)
- [ ] Write **one main question** and **3-5 secondary questions** aligned with available columns.
- [ ] Keep the following baseline question set:
  - [x] **Main question:** Which factors are most associated with severe crashes in Milan, and how should interventions be geographically prioritized?
  - [ ] **Q1:** Which temporal patterns are associated with higher crash severity?
  - [ ] **Q2:** Which Milan areas concentrate disproportionately severe crashes relative to total crashes?
  - [ ] **Q3:** Are road/junction/environment conditions linked to higher odds of severe outcomes?
  - [ ] **Q4:** Can we predict severe vs non-severe crashes with interpretable models?
  - [ ] **Q5:** For later extension, which patterns are city-specific and which are robust across Italy?
- [ ] For each question, specify in one short line:
  - [ ] response variable
  - [ ] predictor candidates
  - [ ] statistical method
  - [ ] evaluation metric
  - [ ] key limitation

### Phase 3 - Data cleaning and preprocessing
- [ ] Remove duplicated crash records.
- [ ] Standardize date/time formats.
- [ ] Standardize categorical labels (severity, weather, road type, district, etc.).
- [ ] Inspect missing values column by column and classify them as:
  - [ ] ignorable
  - [ ] imputable
  - [ ] structurally missing
  - [ ] project-breaking
- [ ] Decide and document treatment of missing values.
- [ ] Detect impossible or suspicious values (negative counts, impossible timestamps, invalid coordinates).
- [ ] Geocode or map crashes to Milan administrative areas if raw coordinates exist.
- [ ] Create derived variables:
  - [ ] hour of day
  - [ ] rush hour indicator
  - [ ] weekend indicator
  - [ ] season
  - [ ] nighttime indicator
  - [ ] junction indicator
  - [ ] central vs peripheral area
  - [ ] severity binary target for classification
- [ ] Create a reproducible preprocessing pipeline in Python, not manual spreadsheet edits.

### Phase 4 - Milan exploratory analysis
- [ ] Produce a clean descriptive profile of the Milan dataset:
  - [ ] number of crashes
  - [ ] years covered
  - [ ] variable coverage
  - [ ] share of severe crashes
- [ ] Create univariate summaries for all main variables.
- [ ] Create bivariate summaries between severity and each key predictor.
- [ ] Make publication-quality visualizations for slides:
  - [ ] severity by hour
  - [ ] severity by weekday/month
  - [ ] hotspot map of all crashes
  - [ ] hotspot map of severe crashes
  - [ ] bar chart of top districts / zones by severe-crash burden
  - [ ] road condition / junction type vs severity
- [ ] Distinguish clearly between **frequency hotspots** and **severity hotspots**.
- [ ] Compute normalized indicators when possible, not only raw counts.
- [ ] Write 5-10 first descriptive findings in plain language.

### Phase 5 - Statistical framing before modeling
- [ ] Decide which tasks are **inference**, which are **prediction**, and which are **unsupervised exploration**.
- [ ] Explicitly justify each method choice in one sentence.
- [ ] Keep the interpretability vs predictive performance trade-off visible throughout the project.
- [ ] Define the primary target variable for supervised models:
  - [ ] severe / non-severe classification as default
- [ ] If severity has more than two levels, decide whether to:
  - [ ] collapse to binary for the core analysis
  - [ ] keep multiclass as an extension
- [ ] Prepare a candidate feature list and remove obvious leakage variables.

### Phase 6 - Inference-first baseline models for Milan
- [ ] Fit an interpretable baseline model first.
- [ ] Preferred order:
  - [ ] contingency tables / association tests for categorical relationships
  - [ ] simple logistic regression
  - [ ] multivariable logistic regression
- [ ] For logistic regression, document:
  - [ ] coding of the target
  - [ ] reference categories
  - [ ] coefficient interpretation
  - [ ] odds ratios with confidence intervals if feasible
- [ ] Check diagnostics and model sanity:
  - [ ] class imbalance
  - [ ] multicollinearity / redundant variables
  - [ ] unstable coefficients
  - [ ] separation issues if present
- [ ] Translate coefficients into plain-language findings useful for policy interpretation.

### Phase 7 - Predictive modeling for Milan
- [ ] Create a train/validation/test workflow or cross-validation pipeline.
- [ ] Define evaluation metrics suited to imbalanced classification:
  - [ ] ROC-AUC
  - [ ] precision / recall
  - [ ] F1
  - [ ] balanced accuracy
  - [ ] confusion matrix
- [ ] Compare a small, justified set of models:
  - [ ] logistic regression baseline
  - [ ] decision tree
  - [ ] k-NN if data scaling makes sense
  - [ ] tree ensemble if available and justified
- [ ] Use model selection and cross-validation, not a single lucky split.
- [ ] If classes are imbalanced, test one principled mitigation strategy:
  - [ ] class weights
  - [ ] resampling
  - [ ] threshold tuning
- [ ] Do not keep a black-box model unless it clearly adds value beyond the interpretable baseline.
- [ ] Summarize which variables matter most for prediction and whether this aligns with the inferential analysis.

### Phase 8 - Unsupervised and spatial insight layer
- [ ] Add one unsupervised component only if it answers a real question.
- [ ] Strong options:
  - [ ] cluster Milan areas by crash profile
  - [ ] PCA on engineered area-level indicators before clustering
  - [ ] detect anomalous areas with unusual crash/severity combinations
- [ ] If using clustering, justify:
  - [ ] input features
  - [ ] scaling choice
  - [ ] number of clusters or clustering criterion
  - [ ] validation approach
- [ ] Interpret clusters substantively (e.g. nightlife-risk zones, commuter corridors, residential low-severity areas).
- [ ] Make sure the unsupervised block creates new insight, not just a colorful plot.

### Phase 9 - Robustness and limitations for Milan
- [ ] Test whether the main findings remain similar under alternative specifications.
- [ ] Examples of robustness checks:
  - [ ] different severity encoding
  - [ ] excluding rows with high missingness
  - [ ] comparing yearly subsets
  - [ ] simpler vs richer feature sets
- [ ] Write a limitations list early, not only at the end:
  - [ ] observational data, not causal proof
  - [ ] under-reporting or reporting bias
  - [ ] missing exposure denominators (traffic volume, population flows)
  - [ ] inconsistent measurement across time/cities
- [ ] Separate clearly what is **associated with severity** from what **causes severity**.

### Phase 10 - Milan outputs that must exist before extension
- [ ] Final cleaned Milan dataset.
- [ ] Final EDA notebook.
- [ ] Final inferential model notebook.
- [ ] Final predictive model notebook.
- [ ] One table of core findings.
- [ ] One table of model metrics.
- [ ] 6-10 slide-ready figures.
- [ ] One short narrative: â€œIf the project had to stop at Milan, what is the complete story?â€

### Phase 11 - Extension to major Italian cities
- [ ] Select the expansion cities based on data quality first, prestige second.
- [ ] Build a city inclusion checklist:
  - [ ] compatible severity label
  - [ ] enough observations
  - [ ] similar time coverage
  - [ ] comparable spatial detail
  - [ ] usable metadata
- [ ] Construct a harmonized multi-city dataset with a `city` variable.
- [ ] Reproduce the Milan preprocessing pipeline for each city.
- [ ] Create a city comparability report and explicitly list what is not perfectly aligned.
- [ ] Start with descriptive cross-city analysis:
  - [ ] crash totals
  - [ ] severe share
  - [ ] temporal patterns
  - [ ] spatial concentration patterns
- [ ] Then move to modeling extensions:
  - [ ] pooled model with city fixed effects / city dummies
  - [ ] city-specific models
  - [ ] compare coefficients or feature importance across cities
- [ ] Ask the key extension question: **Do the determinants of severe crashes generalize across cities, or are they local?**

### Phase 12 - High-grade comparative analysis
- [ ] Produce at least one result that goes beyond â€œMilan but biggerâ€.
- [ ] Candidate comparative questions:
  - [ ] Is Milan structurally different from other cities in severity composition?
  - [ ] Are nighttime effects stronger in some cities than others?
  - [ ] Do junction-related risks generalize across urban contexts?
  - [ ] Which cities are most predictable vs least predictable from available variables?
- [ ] Distinguish three levels of conclusions:
  - [ ] Milan-specific findings
  - [ ] cross-city common patterns
  - [ ] city-specific anomalies worth discussing
- [ ] If possible, create a ranked intervention-priority framework per city.

### Phase 13 - Final deliverables
- [ ] Build the final presentation around **questions -> method -> result -> interpretation -> limitation**.
- [ ] Keep every slide minimal and defensible.
- [ ] Mandatory final deck structure:
  - [ ] motivation and policy relevance
  - [ ] data sources and scope
  - [ ] research questions
  - [ ] preprocessing choices
  - [ ] Milan EDA
  - [ ] Milan inferential results
  - [ ] Milan predictive results
  - [ ] Milan unsupervised/spatial insight
  - [ ] extension to Italian cities
  - [ ] comparative findings
  - [ ] limitations
  - [ ] final implications
- [ ] Prepare a 30-second explanation for every model used.
- [ ] Prepare oral-defense answers for each team member.

### Phase 14 - Oral exam defense prep
- [ ] Prepare for questions on:
  - [ ] why this dataset
  - [ ] why these research questions
  - [ ] why these methods instead of others
  - [ ] assumptions of logistic regression / classification methods
  - [ ] class imbalance handling
  - [ ] cross-validation design
  - [ ] interpretation vs prediction trade-off
  - [ ] limitations and non-causal nature of conclusions
- [ ] Make sure each team member can explain at least one figure, one model, one limitation, and one design decision.

## Recommended statistical storyline
- Start from **descriptive and inferential clarity** in Milan.
- Then add **prediction** to show whether severe crashes are meaningfully predictable.
- Then add **spatial/unsupervised structure** to discover patterns not obvious from raw tables.
- Finally test **generalization across cities**, which is where the project becomes stronger and more original.

## Minimum viable methods set
- [ ] Descriptive statistics and visualization
- [ ] Contingency analysis / association checks
- [ ] Logistic regression
- [ ] Model diagnostics / interpretation
- [ ] Cross-validation and classification metrics
- [ ] One non-linear model comparison
- [ ] One unsupervised or clustering block
- [ ] One cross-city comparative model

## What will maximize the grade
- [ ] Ask a question that feels policy-relevant and non-trivial.
- [ ] Use methods from the course intentionally and explain why they fit.
- [ ] Balance interpretability and predictive performance instead of chasing accuracy only.
- [ ] Show robustness checks and acknowledge limitations honestly.
- [ ] Produce clean, readable visuals and a coherent narrative.
- [ ] Include at least one insight that is not obvious from simple counts.
- [ ] Make the Milan-to-Italy extension methodologically clean, not improvised.

## Expansion plans

### Expansion A - Best grade / safest option
- [ ] Milan full analysis
- [ ] Add 3-5 major cities with harmonized variables
- [ ] Pooled classification model + city comparison
- [ ] Show which findings generalize and which do not
- Why this is strong:
  - [ ] broad scope without becoming unmanageable
  - [ ] clear comparative insight
  - [ ] easy to defend statistically

### Expansion B - Spatial policy focus
- [ ] Milan hotspot and severity geography
- [ ] Compare hotspot structures across cities
- [ ] Cluster neighborhoods/areas by crash risk profile
- [ ] Build an intervention-priority scorecard
- Why this is strong:
  - [ ] visually compelling presentation
  - [ ] high practical relevance
  - [ ] strong â€œnew insightâ€ potential

### Expansion C - Time-pattern focus
- [ ] Study seasonality, weekday patterns, rush hours, night effects
- [ ] Compare temporal signatures across cities
- [ ] Test whether severe crashes spike under similar temporal conditions everywhere
- Why this is strong:
  - [ ] easy to communicate
  - [ ] naturally suited to statistical comparison
  - [ ] useful if spatial variables are weak or inconsistent

### Expansion D - Model comparison focus
- [ ] Use Milan as a benchmark city
- [ ] Compare interpretable vs non-linear models on severity prediction
- [ ] Repeat on other cities to test transferability
- Why this is strong:
  - [ ] directly linked to course themes on prediction vs interpretation
  - [ ] strong oral-defense material
  - [ ] useful if you want a more ML-flavored project without losing statistics

### Expansion E - Equity / urban heterogeneity focus
- [ ] Compare central vs peripheral zones
- [ ] Analyze whether severity risk is concentrated in specific urban contexts
- [ ] Replicate the same segmentation across cities
- Why this is strong:
  - [ ] more original than generic accident counting
  - [ ] can produce non-obvious policy discussion
  - [ ] works well with clustering and area-level summaries

## Stretch goals only if the core is already solid
- [ ] Build a severity risk dashboard for slides/demo.
- [ ] Add external context variables if aligned and feasible (weather, population density, road network features, public transport nodes).
- [ ] Try hierarchical / multilevel modeling if the multi-city data quality is strong enough.
- [ ] Study network structure if the road graph can be constructed meaningfully.
- [ ] Add a simple early-warning framing for severe-crash risk periods or zones.

## Anti-patterns to avoid
- [ ] Do not jump into models before defining the research questions.
- [ ] Do not use many methods without a reason.
- [ ] Do not present only maps and counts; add inference and validation.
- [ ] Do not overclaim causality.
- [ ] Do not expand to too many cities before Milan is fully solved.
- [ ] Do not keep inconsistent city datasets in the same analysis without documenting harmonization limits.
- [ ] Do not rely on one metric only for classification.

## Final checklist before submission
- [ ] The main question is clear in one sentence.
- [ ] Every method answers a specific question.
- [ ] Milan alone already forms a complete project.
- [ ] The extension to Italian cities adds genuine comparative value.
- [ ] At least one result is surprising or non-obvious.
- [ ] Every team member can defend methods and limitations.
- [ ] The slide deck is clean, short, and logically ordered.
- [ ] All code is reproducible from raw data to final figures.
