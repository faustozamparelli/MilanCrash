# MilanCrash
1. Install uv: https://github.com/astral-sh/uv
2. Install dependencies with uv:
```bash
uv sync
```
3. Download the 5 core Milano crash datasets:
```bash
uv run python scripts/data_milan.py
```
4. Run [Processed](./notebooks/Processed.ipynb) to populate ./data/processed/


Please take into consideration [TODO](./TODO.md)