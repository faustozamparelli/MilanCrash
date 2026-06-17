# Raw Data Notes

Scope: this file tracks the original raw inputs and the exact cleaning logic currently used in notebooks/MilanCrashesProcessing.ipynb, notebooks/DrugUseProcessing.ipynb, and notebooks/VehiclesProcessing.ipynb.

## Raw files and columns
All files have a Year column and all starting with milan except milan_vehicle_fleet have a Month column.

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

### 6) euda_wastewater_ww2026_all_cities.csv
- Year
- Metabolite
- Site ID
- Country
- City
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday
- Monday
- Tuesday
- Weekday mean
- Weekend mean
- Daily mean

### 7) milan_vehicle_fleet.csv
- Anno
- AUTOBUS
- AUTOCARRI TRASPORTO MERCI
- AUTOVEICOLI SPECIALI - SPECIFICI
- AUTOVETTURE
- MOTOCARRI E QUADRICICLI TRASPORTO MERCI
- MOTOCICLI
- MOTOVEICOLI E QUADRICICLI SPECIALI - SPECIFICI
- RIMORCHI E SEMIRIMORCHI SPECIALI - SPECIFICI
- RIMORCHI E SEMIRIMORCHI TRASPORTO MERCI
- TRATTORI STRADALI O MOTRICI
- ALTRI VEICOLI

## What we observed in raw

- Files are semicolon-separated (example: `Anno; Mese; IncidentiMortali; ...`).
- Some headers/values contain extra spaces around text/numbers (example: `2024;    5;                4; ...`).
- Empty cells exist (especially in vehicle-count breakdown columns) (example: rows ending with `...;2;0;5;;;;;;`).
- Mixed typing can appear in text-like columns that may actually be numeric (example: numeric IDs such as `Municipio` may arrive as text with spaces, like `"         8"`).
- EUDA wastewater file is comma-separated with quoted headers/values.
- EUDA wastewater file requires `latin1` decoding (plain `utf-8` raises decoding errors).
- Vehicle fleet file is semicolon-separated and includes non-breaking spaces in some headers (normalized during cleaning).

## Cleaning currently implemented in MilanCrashesProcessing.ipynb

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

## Cleaning currently implemented in DrugUseProcessing.ipynb

1. Read `euda_wastewater_ww2026_all_cities.csv` with encoding fallback (`utf-8`, `utf-8-sig`, `latin1`).
2. Trim whitespace from all headers and key string columns (`City`, `Metabolite`, `Country`, `Site ID`).
3. Coerce `Year` to numeric `Int64` and wastewater measure columns to numeric.
4. Remove duplicate rows.
5. Sort rows by `Year`, `Country`, `City`, `Metabolite`.
6. Save mirror cleaned output as `data/processed/euda_wastewater_ww2026_all_cities_cleaned.csv`.

## Cleaning currently implemented in VehiclesProcessing.ipynb

1. Read `milan_vehicle_fleet.csv` with separator `;` and encoding `utf-8-sig`.
2. Normalize column names by replacing non-breaking spaces, collapsing repeated spaces, and trimming whitespace.
3. Coerce `Anno` to numeric `Int64`.
4. Coerce all other measure columns to numeric, round, and store as `Int64`.
5. Remove duplicate rows.
6. Sort rows by `Anno`.
7. Save mirror cleaned output as `data/processed/milan_vehicle_fleet_cleaned.csv`.