# Raw Data Notes

Scope: this file tracks the original raw inputs and the exact cleaning logic currently used in notebooks/Processed.ipynb.

## Raw files and columns

### 1) milan_crashes_monthly.csv
- Anno
- Mese
- IncidentiMortali
- IncidentiSoliFeriti
- Morti
- Feriti

### 2) milan_crashes_monthly_city_ring.csv
- Anno
- Mese
- Cerchia
- Incidenti
- Morti
- Feriti

### 3) milan_crashes_by_nature.csv
- Anno
- Mese
- NaturaIncidente
- Incidenti
- Feriti
- Morti

### 4) milan_crashes_by_vehicles.csv
- Anno
- Mese
- incidenti1veicolo
- morti1veicolo
- feriti1veicolo
- incidenti2veicoli
- morti2veicoli
- feriti2veicoli
- incidenti3veicoli
- morti3veicoli
- feriti3veicoli
- incidenti4veicoli
- morti4veicoli
- feriti4veicoli
- incidenti5veicoli
- morti5veicoli
- feriti5veicoli
- incidenti6veicoli
- morti6veicoli
- feriti6veicoli
- incidenti7epiuveicoli
- morti7epiuveicoli
- feriti7epiuveicoli
- incidentiND
- mortiND
- feritiND

### 5) milan_crashes_by_zone.csv
- Anno
- Mese
- Municipio
- Incidenti
- Feriti
- Morti

## What we observed in raw

- Files are semicolon-separated (example: `Anno; Mese; IncidentiMortali; ...`).
- Some headers/values contain extra spaces around text/numbers (example: `2024;    5;                4; ...`).
- Empty cells exist (especially in vehicle-count breakdown columns) (example: rows ending with `...;2;0;5;;;;;;`).
- Mixed typing can appear in text-like columns that may actually be numeric (example: numeric IDs such as `Municipio` may arrive as text with spaces, like `"         8"`).

## Cleaning currently implemented in Processed.ipynb

1. Read each CSV with separator ; and encoding utf-8-sig.
2. Trim whitespace from all column names.
3. Convert Anno and Mese to numeric Int64 (invalid values become NA).
4. For ID columns (dataset-specific):
- If string/object, trim whitespace and convert empty strings to NA.
5. For non-ID string/object columns:
- Trim whitespace and convert empty strings to NA.
- Try numeric conversion; if more than 80% of values convert, keep numeric version, else keep string version.
6. If both Anno and Mese exist, create month_start as first day of month.
7. Dataset-specific fixes:
- milan_crashes_by_zone: force Municipio to numeric Int64 (unknown stays NA).
- milan_crashes_by_nature: normalize NaturaIncidente by collapsing repeated spaces and removing spaces around hyphens.
8. For numeric measure columns (excluding ID columns and month_start): round values and cast to Int64.
9. Remove duplicate rows.
10. Sort rows by Anno, Mese, then remaining ID columns.
11. Reset index.

## Quality checks currently run

- rows_before, rows_after, duplicates_removed
- missing_cells
- invalid_month_rows (Mese outside 1-12 or missing)
- negative_numeric_cells