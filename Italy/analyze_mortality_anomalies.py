#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze unusually deadly and injury-heavy years by cause and road-user type."""

from __future__ import annotations

from pathlib import Path
import re
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

try:
    import seaborn as sns

    sns.set_theme(style="whitegrid")
except Exception:
    sns = None


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PLOTS_DIR = SCRIPT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

WIDE_FILE = PROJECT_DIR / "istat_incidenti_cause_2007_2024_wide.csv"
RESIDUAL_CAUSE_RE = r"Altre circostanze|imprecisate|concomitanti"

MORTI_COLS = {
    "Conducenti": "morti_conducenti",
    "Trasportati": "morti_trasportati",
    "Pedoni": "morti_pedoni",
}
FERITI_COLS = {
    "Conducenti": "feriti_conducenti",
    "Trasportati": "feriti_trasportati",
    "Pedoni": "feriti_pedoni",
}
CATEGORY_COLORS = {
    "Conducenti": "#006DFF",
    "Trasportati": "#00A35C",
    "Pedoni": "#FF8A00",
}
MORTI_COLOR = "#7A4CC2"
FERITI_COLOR = "#1F8A70"
BASELINE_COLOR = "#4F6F52"
ANOMALY_COLOR = "#C44E52"
COMPARISON_COLOR = "#6A7F9A"


def slugify(value: str) -> str:
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")[:100] or "plot"


def save_figure(fig: plt.Figure, name: str) -> Path:
    path = PLOTS_DIR / f"01_{slugify(name)}.png"
    fig.savefig(path, dpi=170, bbox_inches="tight")
    print(f"Saved plot: {path}")
    plt.close(fig)
    return path


def wrap_label(value: str, width: int = 48) -> str:
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False))


def clean_cause_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["causa"] = df["causa"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["causa"] = df["causa"].str.replace("sustanze", "sostanze", case=False)
    df["macro_categoria"] = (
        df["macro_categoria"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )

    def add_context_tag(row: pd.Series) -> str:
        if row["tipo_riga"] != "causa_specifica":
            return row["causa"]

        macro = str(row["macro_categoria"]).lower()
        if "conducente" in macro:
            tag = "[Conducente]"
        elif "pedon" in macro:
            tag = "[Pedone]"
        elif "evitati" in macro:
            tag = "[Ostacoli/Evitati]"
        elif "urtati" in macro:
            tag = "[Ostacoli/Urtati]"
        else:
            tag = "[Contesto]"
        return f"{tag} {row['causa']}"

    df["causa"] = df.apply(add_context_tag, axis=1)
    return df


def local_baseline(series: pd.Series, years: pd.Series, window: int = 3) -> pd.Series:
    baselines = []
    data = pd.DataFrame({"anno": years, "value": series}).sort_values("anno")
    for _, row in data.iterrows():
        year = int(row["anno"])
        peers = data[data["anno"].between(year - window, year + window) & data["anno"].ne(year)]
        if len(peers) < window:
            peers = data.assign(distance=(data["anno"] - year).abs())
            peers = peers[peers["anno"].ne(year)].nsmallest(window * 2, "distance")
        baselines.append(peers["value"].median())
    return pd.Series(baselines, index=data.index).sort_index()


def add_rate_columns(totals: pd.DataFrame) -> pd.DataFrame:
    totals = totals.sort_values("anno").copy()
    rate_specs = {
        "mortalita": ("morti_totale", "morti_per_1000_incidenti"),
        "feriti": ("feriti_totale", "feriti_per_1000_incidenti"),
    }
    for category, col in MORTI_COLS.items():
        rate_specs[f"morti_{category.lower()}"] = (col, f"{col}_per_1000_incidenti")
    for category, col in FERITI_COLS.items():
        rate_specs[f"feriti_{category.lower()}"] = (col, f"{col}_per_1000_incidenti")

    for _, (count_col, rate_col) in rate_specs.items():
        totals[rate_col] = totals[count_col] / totals["incidenti"].replace(0, np.nan) * 1000
        baseline_col = f"baseline_{rate_col}"
        pct_col = f"scostamento_{rate_col}_pct"
        totals[baseline_col] = local_baseline(totals[rate_col], totals["anno"])
        totals[pct_col] = (totals[rate_col] / totals[baseline_col].replace(0, np.nan) - 1) * 100
    return totals


def high_outlier_years(
    totals: pd.DataFrame,
    rate_col: str,
    threshold_pct: float = 5.0,
    start_year: int | None = None,
    fallback_top: int = 3,
) -> list[int]:
    pct_col = f"scostamento_{rate_col}_pct"
    data = totals.copy()
    if start_year is not None:
        data = data[data["anno"].ge(start_year)]
    selected = data[data[pct_col].ge(threshold_pct)].sort_values(pct_col, ascending=False)
    if selected.empty:
        selected = data[data[pct_col].gt(0)].sort_values(pct_col, ascending=False).head(fallback_top)
    return selected["anno"].astype(int).tolist()


def comparison_years_for(
    totals: pd.DataFrame, anomaly_year: int, rate_col: str, n_years: int = 4
) -> list[int]:
    row = totals[totals["anno"].eq(anomaly_year)].iloc[0]
    candidates = totals[totals["anno"].ne(anomaly_year)].copy()
    lower = candidates[candidates[rate_col].lt(row[rate_col])]
    if len(lower) >= n_years:
        candidates = lower
    candidates["distance"] = (candidates["anno"] - anomaly_year).abs()
    return (
        candidates.sort_values(["distance", rate_col])
        .head(n_years)["anno"]
        .astype(int)
        .tolist()
    )


def plot_total_anomaly_timeline(
    totals: pd.DataFrame,
    rate_col: str,
    baseline_col: str,
    pct_col: str,
    outlier_years: list[int],
    title: str,
    ylabel: str,
    save_name: str,
    color: str,
    threshold_line: float,
) -> None:
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [2.1, 1]},
    )

    axes[0].plot(
        totals["anno"],
        totals[rate_col],
        marker="o",
        color=color,
        linewidth=2.5,
        label=ylabel,
    )
    axes[0].plot(
        totals["anno"],
        totals[baseline_col],
        linestyle="--",
        color=BASELINE_COLOR,
        linewidth=2,
        label="Baseline locale (mediana anni vicini)",
    )
    for year in outlier_years:
        row = totals[totals["anno"].eq(year)].iloc[0]
        axes[0].scatter(
            row["anno"],
            row[rate_col],
            s=120,
            color=ANOMALY_COLOR,
            edgecolor="white",
            linewidth=1.5,
            zorder=5,
        )
        axes[0].annotate(
            f"{int(year)}\n{row[rate_col]:.1f}",
            xy=(row["anno"], row[rate_col]),
            xytext=(0, 16),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=ANOMALY_COLOR,
            fontweight="bold",
        )
    axes[0].set_title(title)
    axes[0].set_ylabel(ylabel)
    axes[0].legend(loc="best")
    axes[0].grid(True, linestyle="--", alpha=0.35)

    bar_colors = [
        ANOMALY_COLOR if int(year) in outlier_years else COMPARISON_COLOR
        for year in totals["anno"]
    ]
    axes[1].bar(totals["anno"], totals[pct_col], color=bar_colors)
    axes[1].axhline(0, color="#333333", linewidth=1)
    axes[1].axhline(threshold_line, color=ANOMALY_COLOR, linewidth=1, linestyle=":")
    axes[1].set_ylabel("Scostamento %")
    axes[1].set_xlabel("Anno")
    axes[1].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:+.0f}%"))
    axes[1].set_xticks(totals["anno"].astype(int).tolist())
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(True, axis="y", linestyle="--", alpha=0.35)

    fig.tight_layout()
    save_figure(fig, save_name)


def plot_category_anomaly_timeline(
    totals: pd.DataFrame,
    category_cols: dict[str, str],
    prefix: str,
    title: str,
    ylabel: str,
    save_name: str,
) -> dict[str, list[int]]:
    fig, axes = plt.subplots(1, 3, figsize=(21, 6), sharex=True)
    outliers_by_category = {}

    for ax, (category, count_col) in zip(axes, category_cols.items()):
        rate_col = f"{count_col}_per_1000_incidenti"
        baseline_col = f"baseline_{rate_col}"
        pct_col = f"scostamento_{rate_col}_pct"
        threshold = 5.0 if prefix == "morti" else 3.0
        outliers = high_outlier_years(totals, rate_col, threshold_pct=threshold, fallback_top=2)
        outliers_by_category[category] = outliers

        ax.plot(
            totals["anno"],
            totals[rate_col],
            marker="o",
            color=CATEGORY_COLORS[category],
            linewidth=2.3,
            label=ylabel,
        )
        ax.plot(
            totals["anno"],
            totals[baseline_col],
            linestyle="--",
            color=BASELINE_COLOR,
            linewidth=1.8,
            label="Baseline locale",
        )
        for year in outliers:
            row = totals[totals["anno"].eq(year)].iloc[0]
            ax.scatter(row["anno"], row[rate_col], s=95, color=ANOMALY_COLOR, zorder=5)
            ax.annotate(
                str(year),
                xy=(row["anno"], row[rate_col]),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=ANOMALY_COLOR,
                fontweight="bold",
            )
        ax.set_title(category)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Anno")
        ax.set_xticks(totals["anno"].astype(int).tolist()[::2])
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(fontsize=8, loc="best")

    fig.suptitle(title, y=1.04, fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, save_name)
    return outliers_by_category


def cause_category_rates(
    cause_df: pd.DataFrame,
    years: list[int],
    category_cols: dict[str, str],
    value_name: str,
    label: str,
) -> pd.DataFrame:
    subset = cause_df[cause_df["anno"].isin(years)]
    year_count = len(years)
    frames = []
    for category, value_col in category_cols.items():
        grouped = (
            subset.groupby("causa", as_index=False)
            .agg(value=(value_col, "sum"), incidenti=("incidenti", "sum"))
            .assign(
                categoria=category,
                periodo=label,
                value_annuo=lambda x: x["value"] / year_count,
                incidenti_annui=lambda x: x["incidenti"] / year_count,
                tasso_per_1000_incidenti=lambda x: x["value"]
                / x["incidenti"].replace(0, np.nan)
                * 1000,
                misura=value_name,
            )
        )
        frames.append(grouped)
    return pd.concat(frames, ignore_index=True)


def plot_delta_heatmap_for_year(
    cause_df: pd.DataFrame,
    totals: pd.DataFrame,
    anomaly_year: int,
    rate_col: str,
    category_cols: dict[str, str],
    value_name: str,
    min_annual_value: float,
    save_suffix: str,
    cmap: str,
) -> None:
    comparison_years = comparison_years_for(totals, anomaly_year, rate_col)
    comparison_label = f"Confronto {', '.join(map(str, comparison_years))}"
    rates = pd.concat(
        [
            cause_category_rates(cause_df, [anomaly_year], category_cols, value_name, str(anomaly_year)),
            cause_category_rates(
                cause_df, comparison_years, category_cols, value_name, comparison_label
            ),
        ],
        ignore_index=True,
    )
    anomaly = rates[rates["periodo"].eq(str(anomaly_year))]
    comparison = rates[rates["periodo"].eq(comparison_label)]
    merged = anomaly.merge(
        comparison,
        on=["causa", "categoria", "misura"],
        suffixes=("_anno", "_confronto"),
        how="left",
    )
    merged["delta_tasso"] = (
        merged["tasso_per_1000_incidenti_anno"]
        - merged["tasso_per_1000_incidenti_confronto"].fillna(0)
    )
    merged["value_totale_anno"] = merged.groupby("causa")["value_annuo_anno"].transform("sum")
    relevant = merged[merged["value_totale_anno"].ge(min_annual_value)].copy()
    if relevant.empty:
        relevant = merged.copy()

    top_causes = (
        relevant.groupby("causa", as_index=False)
        .agg(delta_medio=("delta_tasso", "mean"), value_anno=("value_totale_anno", "max"))
        .assign(score=lambda x: np.maximum(x["delta_medio"], 0) * x["value_anno"])
        .sort_values("score", ascending=False)
        .head(14)["causa"]
        .tolist()
    )
    heat = (
        merged[merged["causa"].isin(top_causes)]
        .pivot_table(index="causa", columns="categoria", values="delta_tasso", aggfunc="mean")
        .reindex(columns=list(category_cols.keys()))
    )
    heat = heat.loc[
        merged[merged["causa"].isin(top_causes)]
        .groupby("causa")["value_totale_anno"]
        .max()
        .sort_values()
        .index
    ]

    fig, ax = plt.subplots(figsize=(11.5, 9))
    color_label = (
        f"Delta {value_name.lower()} per 1.000 incidenti "
        f"({anomaly_year} - confronto)"
    )
    if sns is not None:
        sns.heatmap(
            heat,
            annot=True,
            fmt=".1f",
            cmap=cmap,
            center=0,
            linewidths=0.5,
            cbar_kws={"label": color_label},
            ax=ax,
        )
    else:
        image = ax.imshow(heat.fillna(0), cmap=cmap)
        fig.colorbar(image, ax=ax, label=color_label)
        ax.set_xticks(np.arange(len(heat.columns)), labels=heat.columns)
        ax.set_yticks(np.arange(len(heat.index)), labels=heat.index)

    ax.set_yticklabels([wrap_label(label.get_text(), 48) for label in ax.get_yticklabels()])
    ax.set_title(f"{value_name}: cause sopra confronto nel {anomaly_year}")
    ax.set_xlabel("Tipo di persona coinvolta")
    ax.set_ylabel("Causa")
    fig.tight_layout()
    save_figure(fig, f"heatmap_delta_{save_suffix}_{anomaly_year}_vs_anni_confronto")


def print_outlier_table(totals: pd.DataFrame, rate_col: str, years: list[int], label: str) -> None:
    pct_col = f"scostamento_{rate_col}_pct"
    print(f"\n{label}")
    print(
        totals[totals["anno"].isin(years)][["anno", rate_col, pct_col]]
        .sort_values(pct_col, ascending=False)
        .to_string(index=False)
    )


def main() -> None:
    df = clean_cause_labels(pd.read_csv(WIDE_FILE))
    totals = add_rate_columns(df[df["tipo_riga"].eq("totale")].copy())
    cause_df = df[df["tipo_riga"].eq("causa_specifica")].copy()
    cause_df = cause_df[
        ~cause_df["causa"].str.contains(RESIDUAL_CAUSE_RE, case=False, na=False)
    ].copy()

    deadly_years_all = high_outlier_years(
        totals, "morti_per_1000_incidenti", threshold_pct=5.0, fallback_top=3
    )
    deadly_years_modern = high_outlier_years(
        totals, "morti_per_1000_incidenti", threshold_pct=5.0, start_year=2014, fallback_top=1
    )
    injury_years = high_outlier_years(
        totals, "feriti_per_1000_incidenti", threshold_pct=5.0, fallback_top=3
    )

    plot_total_anomaly_timeline(
        totals,
        "morti_per_1000_incidenti",
        "baseline_morti_per_1000_incidenti",
        "scostamento_morti_per_1000_incidenti_pct",
        deadly_years_modern,
        "Anni moderni con mortalita per incidente sopra la baseline locale",
        "Morti per 1.000 incidenti",
        "mortalita_per_incidente_anni_anomali",
        MORTI_COLOR,
        threshold_line=5.0,
    )
    plot_total_anomaly_timeline(
        totals,
        "feriti_per_1000_incidenti",
        "baseline_feriti_per_1000_incidenti",
        "scostamento_feriti_per_1000_incidenti_pct",
        injury_years,
        "Anni con feriti per incidente sopra la baseline locale",
        "Feriti per 1.000 incidenti",
        "feriti_per_incidente_anni_anomali",
        FERITI_COLOR,
        threshold_line=1.0,
    )

    morti_category_outliers = plot_category_anomaly_timeline(
        totals,
        MORTI_COLS,
        "morti",
        "Mortalita per incidente per tipo di persona coinvolta",
        "Morti per 1.000 incidenti",
        "mortalita_per_incidente_per_tipo_persona_coinvolta",
    )
    feriti_category_outliers = plot_category_anomaly_timeline(
        totals,
        FERITI_COLS,
        "feriti",
        "Feriti per incidente per tipo di persona coinvolta",
        "Feriti per 1.000 incidenti",
        "feriti_per_incidente_per_tipo_persona_coinvolta",
    )

    for year in deadly_years_all[:4]:
        plot_delta_heatmap_for_year(
            cause_df,
            totals,
            year,
            "morti_per_1000_incidenti",
            MORTI_COLS,
            "Morti",
            min_annual_value=5,
            save_suffix="morti",
            cmap="RdBu_r",
        )

    feriti_category_scores = {}
    for _, count_col in FERITI_COLS.items():
        rate_col = f"{count_col}_per_1000_incidenti"
        pct_col = f"scostamento_{rate_col}_pct"
        for _, row in totals[totals["anno"].ge(2014)].iterrows():
            year = int(row["anno"])
            feriti_category_scores[year] = max(feriti_category_scores.get(year, -np.inf), row[pct_col])

    injury_heatmap_years = [
        year
        for year, _ in sorted(feriti_category_scores.items(), key=lambda item: item[1], reverse=True)
        if year in {candidate for years in feriti_category_outliers.values() for candidate in years}
    ][:4]
    for year in injury_heatmap_years:
        plot_delta_heatmap_for_year(
            cause_df,
            totals,
            year,
            "feriti_per_1000_incidenti",
            FERITI_COLS,
            "Feriti",
            min_annual_value=100,
            save_suffix="feriti",
            cmap="BrBG",
        )

    print_outlier_table(totals, "morti_per_1000_incidenti", deadly_years_all, "Anni overly deadly")
    print_outlier_table(totals, "feriti_per_1000_incidenti", injury_years, "Anni overly feriti")
    print("\nOutlier morti per tipo:", morti_category_outliers)
    print("Outlier feriti per tipo:", feriti_category_outliers)


if __name__ == "__main__":
    main()
