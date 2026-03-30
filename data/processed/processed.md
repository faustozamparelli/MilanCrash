# Processed Datasets Reference

This document describes the cleaned files in `data/processed/` and explains each column.

## 1) milan_crashes_monthly_cleaned.csv

**Granularity:** one row per month (city-wide).

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `IncidentiMortali` (`8`): number of fatal crashes in the month.
- `IncidentiSoliFeriti` (`1225`): number of crashes with injuries only (no deaths).
- `Morti` (`8`): total people killed in the month.
- `Feriti` (`1690`): total people injured in the month.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).

## 2) milan_crashes_monthly_city_ring_cleaned.csv

**Granularity:** one row per month and city-ring area (`Cerchia`).

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `Cerchia` (`Entro la Cerchia dei Navigli`): ring-area category inside Milan (text label from source dataset).
- `Incidenti` (`88`): number of crashes in that month and ring area.
- `Morti` (`0`): number of people killed in that month and ring area.
- `Feriti` (`106`): number of people injured in that month and ring area.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).

## 3) milan_crashes_by_nature_cleaned.csv

**Granularity:** one row per month and crash nature (`NaturaIncidente`).

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `NaturaIncidente` (`Altre cause`): crash type/cause category (normalized text labels).
- `Incidenti` (`37`): number of crashes in that month and nature category.
- `Feriti` (`37`): number of injured people in that month and nature category.
- `Morti` (`0`): number of killed people in that month and nature category.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).

## 4) milan_crashes_by_vehicles_cleaned.csv

**Granularity:** one row per month, split by number of vehicles involved.

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `incidenti1veicolo` (`364`): crashes involving 1 vehicle.
- `morti1veicolo` (`3`): deaths in crashes involving 1 vehicle.
- `feriti1veicolo` (`407`): injuries in crashes involving 1 vehicle.
- `incidenti2veicoli` (`695`): crashes involving 2 vehicles.
- `morti2veicoli` (`5`): deaths in crashes involving 2 vehicles.
- `feriti2veicoli` (`982`): injuries in crashes involving 2 vehicles.
- `incidenti3veicoli` (`123`): crashes involving 3 vehicles.
- `morti3veicoli` (`0`): deaths in crashes involving 3 vehicles.
- `feriti3veicoli` (`212`): injuries in crashes involving 3 vehicles.
- `incidenti4veicoli` (`35`): crashes involving 4 vehicles.
- `morti4veicoli` (`0`): deaths in crashes involving 4 vehicles.
- `feriti4veicoli` (`68`): injuries in crashes involving 4 vehicles.
- `incidenti5veicoli` (`10`): crashes involving 5 vehicles.
- `morti5veicoli` (`0`): deaths in crashes involving 5 vehicles.
- `feriti5veicoli` (`15`): injuries in crashes involving 5 vehicles.
- `incidenti6veicoli` (`4`): crashes involving 6 vehicles.
- `morti6veicoli` (`0`): deaths in crashes involving 6 vehicles.
- `feriti6veicoli` (`4`): injuries in crashes involving 6 vehicles.
- `incidenti7epiuveicoli` (`2`): crashes involving 7 or more vehicles.
- `morti7epiuveicoli` (`0`): deaths in crashes involving 7 or more vehicles.
- `feriti7epiuveicoli` (`2`): injuries in crashes involving 7 or more vehicles.
- `incidentiND` (`0`): crashes with unknown number of vehicles (`ND` = not available).
- `mortiND` (`0`): deaths where vehicle-count class is unknown.
- `feritiND` (`0`): injuries where vehicle-count class is unknown.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).
- `incidenti_tot_veicoli` (`1233`): total crashes from all vehicle-count classes (sum of all columns starting with `incidenti`).

## 5) milan_crashes_by_zone_cleaned.csv

**Granularity:** one row per month and Milan municipality zone (`Municipio`).

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `Municipio` (`1`): municipality/district ID (1-9, missing allowed if unknown).
- `Incidenti` (`171`): number of crashes in that month and municipality.
- `Feriti` (`209`): number of injured people in that month and municipality.
- `Morti` (`0`): number of killed people in that month and municipality.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).

## 6) milan_crashes_monthly_features.csv

**Granularity:** one row per month (city-wide), with engineered features.

Columns:
- `Anno` (`2001`): calendar year.
- `Mese` (`1`): month number (1-12).
- `IncidentiMortali` (`8`): number of fatal crashes in the month.
- `IncidentiSoliFeriti` (`1225`): number of crashes with injuries only.
- `Morti` (`8`): total people killed in the month.
- `Feriti` (`1690`): total people injured in the month.
- `month_start` (`2001-01-01`): first day of the month as date (`YYYY-MM-01`).
- `IncidentiTotali` (`1233`): total monthly crashes, computed as `IncidentiMortali + IncidentiSoliFeriti`.
- `morti_per_100_incidenti` (`0.649`): deaths per 100 crashes, computed as `100 * Morti / IncidentiTotali`.
- `feriti_per_incidente` (`1.371`): average injuries per crash, computed as `Feriti / IncidentiTotali`.
- `is_summer` (`0`): seasonal flag, `1` if month is June/July/August, else `0`.
- `is_winter` (`1`): seasonal flag, `1` if month is December/January/February, else `0`.

## Common Processing Notes

- Empty strings are converted to missing values (`NA`).
- `Anno` and `Mese` are parsed as numeric integer-like columns.
- In `milan_crashes_by_zone_cleaned.csv`, `Municipio` is explicitly coerced to numeric integer-like (`Int64`) values.
- Numeric measure columns are rounded and stored as integer-like values where possible.
- Duplicate rows are removed.
- `month_start` is derived from `Anno` + `Mese` with day fixed to `1`.
- Type coercion/cleaning is performed in `Processed.ipynb`; `Trends.ipynb` is intended to validate schema/types and analyze preprocessed data.
