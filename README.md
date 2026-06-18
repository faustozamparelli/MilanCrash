# MilanCrash

Statistical analysis of road crashes in Italy, with a focused case study on Milan. The project was developed for the Applied Statistics course at Politecnico di Milano and combines national ISTAT crash-cause data with Milan open data to study trends, severity, geography, seasonality, and selected contextual factors.

For the presentation summary, see `ItalyCauseOfCrashes.pptx`.

## Setup

Install `uv`, then install the Python dependencies:

```bash
uv sync
```

## How to Run

### 1. Italy Analysis

The Italy part uses the ISTAT datasets already stored in `Italy/`:

```bash
uv run python Italy/analysis.py
uv run python Italy/analyze_mortality_anomalies.py
```

The scripts read:

- `Italy/istat_incidenti_cause_2007_2024_wide.csv`
- `Italy/istat_incidenti_cause_2007_2024_long.csv`

Generated charts are written to `Italy/plots/`.

### 2. Milan Analysis

Download or refresh the Milan source data:

```bash
uv run python Milan/scripts/crashes_milan.py
uv run python Milan/scripts/drug_wastewater_euda.py
uv run python Milan/scripts/vehicle_fleet_milan.py
```

Then run the cleaning notebooks in `Milan/cleaning/`, followed by the inference notebooks in `Milan/inference/`. The intended order is:

1. `Milan/cleaning/MilanCrashesProcessing.ipynb`
2. `Milan/cleaning/DrugUseProcessing.ipynb`
3. `Milan/cleaning/VehiclesProcessing.ipynb`
4. `Milan/cleaning/AreaCProcessing.ipynb`
5. `Milan/inference/Cerchie.ipynb`
6. `Milan/inference/CerchieSeasonality.ipynb`
7. `Milan/inference/CrashDrugUse.ipynb`
8. `Milan/inference/CrashType.ipynb`
9. `Milan/inference/Fleet.ipynb`
10. `Milan/inference/AreaC.ipynb`

## Project Structure

- `Italy/`: national ISTAT crash-cause analysis, cleaned ISTAT CSV files, and generated plots.
- `Milan/scripts/`: data download and utility scripts for Milan datasets.
- `Milan/data/raw/`: raw Milan open data and external contextual data.
- `Milan/data/processed/`: cleaned tables used by the inference notebooks.
- `Milan/cleaning/`: notebooks that prepare raw data for analysis.
- `Milan/inference/`: statistical notebooks for the Milan case study.
- `Milan/findings.md`: concise summary of the Milan statistical findings.
- `ItalyCauseOfCrashes.pptx`: presentation material for the Italy analysis.

## Statistical Analysis

The Italy analysis studies crash causes from 2007 to 2024, including time trends, deaths and injuries by road-user type, cause rankings, severity rates per 1,000 crashes, anomalous years, correlations between causes, and clustering of cause profiles.

The Milan analysis focuses on city-level risk patterns. It includes ring-based crash density and severity, seasonality tests, Poisson GLMs with exposure offsets, bootstrap confidence intervals, crash-type severity models, trend-adjusted and first-difference correlations for drug and vehicle-fleet variables, multiple-testing correction, and temporal holdout checks for predictive modelling.
