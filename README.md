# MilanCrash
1. Install uv: https://github.com/astral-sh/uv
2. Install dependencies with uv:
```bash
uv sync
```
3. Download the 5 core Milano crash datasets:
```bash
uv run python scripts/crashes_milan.py
```
4. Download the EUDA wastewater dataset (all cities):
```bash
uv run python scripts/drug_wastewater_euda.py
```
5. Run [MilanCrashesProcessing](./notebooks/MilanCrashesProcessing.ipynb) to populate cleaned crash mirror data in ./data/processed/
6. Run [DrugUseProcessing](./notebooks/DrugUseProcessing.ipynb) to populate cleaned wastewater mirror data in ./data/processed/
7. Run [CrashDrugUse](./notebooks/CrashDrugUse.ipynb) to analyze yearly crash-drug correlations with tables/plots 
8. Run [Cerchie](./notebooks/Cerchie.ipynb) to analyze crash patterns by city ring with tables/plots 