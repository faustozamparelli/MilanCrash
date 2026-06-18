#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converted from progetto_istat_incidenti_2007_2024_improved.ipynb.

Markdown cells from the notebook are preserved below as Python comments.
Plots are saved to PLOTS_DIR after each original notebook code cell.
"""

from pathlib import Path
import colorsys
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from IPython.display import display
except Exception:
    def display(obj):
        print(obj)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PLOTS_DIR = SCRIPT_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

_SAVED_FIGURES = 0


def _slugify(value):
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")[:80] or "plot"


def _save_all_figures(label):
    global _SAVED_FIGURES
    for num in plt.get_fignums():
        fig = plt.figure(num)
        _SAVED_FIGURES += 1
        path = PLOTS_DIR / f"{_SAVED_FIGURES:02d}_{_slugify(label)}_fig{num}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Saved plot: {path}")
    plt.close("all")


def _save_named_figures(name):
    for num in plt.get_fignums():
        fig = plt.figure(num)
        path = PLOTS_DIR / f"{_slugify(name)}_fig{num}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"Saved plot: {path}")
    plt.close("all")


def _make_category_palette(categories):
    categories = sorted({str(c) for c in categories if c is not None})
    golden_ratio = 0.618033988749895
    return {
        category: colorsys.hsv_to_rgb((i * golden_ratio) % 1.0, 0.88, 0.96)
        for i, category in enumerate(categories)
    }


USER_CATEGORY_PALETTE = {
    'conducente': '#006DFF',
    'trasportato': '#00B050',
    'pedone': '#FF8A00',
}


# Keep relative file reads anchored to new_project, matching the notebook data files.
DATA_DIR = PROJECT_DIR

# %% [markdown] cell 0
# # Cause degli incidenti stradali gravi in Italia, dati ISTAT 2007-2024
#
# Obiettivo: identificare le circostanze associate al maggior numero di incidenti e alla maggiore mortalita, mantenendo distinte le vittime per categoria di utente della strada: conducenti, persone trasportate e pedoni.
#
# **Nota metodologica importante.** I dati sono aggregati per causa e anno: l'analisi stima associazioni e profili di rischio, non causalita individuale. Per questo, oltre alla regressione lineare richiesta, il notebook usa anche modelli per conteggi, piu adatti a incidenti e decessi.

# %% [markdown] cell 1
# ## 1. Setup
#
# Se mancano librerie nell'ambiente, eseguire una volta:
#
# ```python
# %pip install pandas numpy matplotlib seaborn scikit-learn statsmodels openpyxl
# ```

# %% cell 2
import pandas as pd

# Dice a Pandas di mostrare TUTTE le colonne senza mettere i tre puntini al centro
pd.set_option('display.max_columns', None)

# Dice a Pandas di mostrare TUTTE le righe (occhio se il dataset è gigante, metti es. 100)
pd.set_option('display.max_rows', 10)

# Dice a Pandas di non troncare il testo dentro le celle se è troppo lungo
pd.set_option('display.max_colwidth', None)

_save_all_figures('cell_02_1. Setup')

# %% cell 3
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    sns.set_theme(style='whitegrid')
except Exception:
    sns = None

pd.options.display.float_format = '{:,.2f}'.format
DATA_DIR = PROJECT_DIR
wide_file = DATA_DIR / 'istat_incidenti_cause_2007_2024_wide.csv'
long_file = DATA_DIR / 'istat_incidenti_cause_2007_2024_long.csv'

df = pd.read_csv(wide_file)
df_long = pd.read_csv(long_file)
df.head()

_save_all_figures('cell_03_1. Setup')

# %% [markdown] cell 4
# Questa è solo la testa del file

# %% [markdown] cell 5
# ## 2. Struttura dei dati
#
# Il dataset `wide` conserva tutte le colonne originali importanti: morti e feriti per conducenti, persone trasportate e pedoni. Il dataset `long` serve invece per grafici e modelli in cui la categoria dell'utente colpito e una variabile esplicita.

# %% cell 6
print(df.shape)
display(df[['anno','causa','tipo_riga','macro_categoria','incidenti','morti_conducenti','morti_trasportati','morti_pedoni','morti_totale','feriti_totale']].head(10))
display(df_long.head(12))
df[['incidenti','morti_totale','feriti_totale','mortalita_per_1000_incidenti','quota_morti_pedoni_pct']].describe()

_save_all_figures('cell_06_2. Struttura dei dati')

# %% cell 7
# Controllo di coerenza: il totale morti deve essere la somma delle tre categorie utente.
check = df.assign(diff_morti=df['morti_totale'] - df[['morti_conducenti','morti_trasportati','morti_pedoni']].sum(axis=1),
                  diff_feriti=df['feriti_totale'] - df[['feriti_conducenti','feriti_trasportati','feriti_pedoni']].sum(axis=1))
display(check[['diff_morti','diff_feriti']].abs().describe())
display(check.loc[(check['diff_morti'].abs()>1e-9) | (check['diff_feriti'].abs()>1e-9), ['anno','causa','diff_morti','diff_feriti']].head())

_save_all_figures('cell_07_2. Struttura dei dati')

# %% [markdown] cell 8
# Analisi, microcause ridondanti

# %% cell 9
# Vediamo quali cause specifiche compaiono sotto più di una macro_categoria
df_micro = df[df['tipo_riga'] == 'causa_specifica']
duplicati = df_micro.groupby('causa')['macro_categoria'].nunique()
cause_problematiche = duplicati[duplicati > 1].index.tolist()

print("Cause con lo stesso nome in macro-categorie diverse:")
print(cause_problematiche)

_save_all_figures('cell_09_Analisi, microcause ridondanti')

# %% [markdown] cell 10
# Cella per pulizia di refusi nome e Assegnazione di tag per differenziazione su macro categorie

# %% cell 11
# --- INIZIO FIX RETROATTIVO TOTALMENTE BLINDATO V3 ---

# STEP 1: Pulizia spazi e correzione refusi storici noti dell'ISTAT
df['causa'] = df['causa'].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
# Correggiamo "sustanze" in "sostanze" per unificare la causa negli anni
df['causa'] = df['causa'].str.replace('sustanze', 'sostanze', case=False)

df['macro_categoria'] = df['macro_categoria'].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)

# STEP 2: Funzione che applica il tag a TUTTE le cause specifiche per renderle univoche a prescindere
def assegna_tag_univoco(row):
    if row['tipo_riga'] == 'causa_specifica':
        macro = str(row['macro_categoria']).lower()
        
        # Scegliamo il tag in base alla macro-categoria d'appartenenza
        if 'conducente' in macro:
            tag = "[Conducente]"
        elif 'pedon' in macro:
            tag = "[Pedone]"
        elif 'evitati' in macro:
            tag = "[Ostacoli/Evitati]"
        elif 'urtati' in macro:
            tag = "[Ostacoli/Urtati]"
        else:
            # Se la macro-categoria non è chiara, usiamo il nome del foglio ISTAT
            tag = "[Contesto]"
            
        return f"{tag} {row['causa']}"
    
    return row['causa']

# Applichiamo il fix a tappeto
df['causa'] = df.apply(assegna_tag_univoco, axis=1)
# --- FINE FIX RETROATTIVO ---

# VERIFICA FINALE DEI CASI CRITICI
print("\n--- VERIFICA DEI CASI CRITICI (DOPO FIX V3) ---")
print("Sostanze stupefacenti (Dovresti vedere i tag applicati e una sola dicitura corretta):")
print(df[df['causa'].str.contains('sostanze stupefacenti|ingestione', case=False, na=False)]['causa'].unique())

print("\nCondizioni morbose (Dovrebbero essere separate e taggate chiaramente):")
print(df[df['causa'].str.contains('condizioni morbose|in atto', case=False, na=False)]['causa'].unique())

_save_all_figures('cell_11_Cella per pulizia di refusi nome e Assegnazione di tag per differenziazione su macro categorie')

# %% [markdown] cell 12
# ## 3. EDA Temporale
#
# Qui guardiamo l'evoluzione temporale deu parametri. La riga `Totale` e usata solo per trend generali, non per addestrare modelli sulle cause.

# %% [markdown] cell 13
# Analisi Temporale: Incidenti, Morti, Morti ogni 1000 e Feriti ogni 1000

# %% cell 14
totali = df[df['tipo_riga'].eq('totale')].sort_values('anno')
display(totali[['anno','incidenti','morti_totale','feriti_totale','mortalita_per_1000_incidenti','feriti_per_1000_incidenti']])

anni = totali['anno'].astype(int).tolist()
year_ticks = anni

fig, axes = plt.subplots(1, 3, figsize=(24, 5.5), sharex=False)

axes[0].plot(totali['anno'], totali['incidenti'], marker='o', color='#4c72b0', linewidth=2)
axes[0].set_title('Incidenti totali')
axes[0].set_ylabel('Incidenti')
axes[0].grid(True, linestyle='--', alpha=0.4)

axes[1].plot(totali['anno'], totali['morti_totale'], marker='o', color='#c44e52', linewidth=2, label='Morti totali')
axes[1].set_title('Morti: totale e per 1.000 incidenti')
axes[1].set_ylabel('Morti totali', color='#c44e52')
axes[1].tick_params(axis='y', labelcolor='#c44e52')
axes[1].grid(True, linestyle='--', alpha=0.4)
ax_morti_rate = axes[1].twinx()
ax_morti_rate.plot(totali['anno'], totali['mortalita_per_1000_incidenti'], marker='s', color='#8172b3', linewidth=2, label='Morti per 1.000 incidenti')
ax_morti_rate.set_ylabel('Morti per 1.000 incidenti', color='#8172b3')
ax_morti_rate.tick_params(axis='y', labelcolor='#8172b3')
lines, labels = axes[1].get_legend_handles_labels()
rate_lines, rate_labels = ax_morti_rate.get_legend_handles_labels()
axes[1].legend(lines + rate_lines, labels + rate_labels, loc='upper right', fontsize=8)

axes[2].plot(totali['anno'], totali['feriti_totale'], marker='o', color='#55a868', linewidth=2, label='Feriti totali')
axes[2].set_title('Feriti: totale e per 1.000 incidenti')
axes[2].set_ylabel('Feriti totali', color='#55a868')
axes[2].tick_params(axis='y', labelcolor='#55a868')
axes[2].grid(True, linestyle='--', alpha=0.4)
ax_feriti_rate = axes[2].twinx()
ax_feriti_rate.plot(totali['anno'], totali['feriti_per_1000_incidenti'], marker='s', color='#dd8452', linewidth=2, label='Feriti per 1.000 incidenti')
ax_feriti_rate.set_ylabel('Feriti per 1.000 incidenti', color='#dd8452')
ax_feriti_rate.tick_params(axis='y', labelcolor='#dd8452')
lines, labels = axes[2].get_legend_handles_labels()
rate_lines, rate_labels = ax_feriti_rate.get_legend_handles_labels()
axes[2].legend(lines + rate_lines, labels + rate_labels, loc='upper right', fontsize=8)

for ax in axes:
    ax.set_xlabel('Anno')
    ax.set_xticks(year_ticks)
    ax.set_xticklabels(year_ticks, rotation=45, ha='right')
plt.tight_layout()
plt.show()

_save_all_figures('cell_14_Analisi Temporale: Incidenti, Morti, Morti ogni 1000 e Feriti ogni 1000')

# %% [markdown] cell 15
# Analisi Temporale: Feriti Conducenti, Feriti Trasportati e Feriti Pedoni

# %% cell 16
totali = df[df['tipo_riga'].eq('totale')].sort_values('anno')
display(totali[['anno','feriti_conducenti','feriti_trasportati','feriti_pedoni']])

anni = totali['anno'].astype(int).tolist()
fig, ax = plt.subplots(figsize=(14, 5.5))
for col, label, color in [
    ('feriti_conducenti', 'Feriti conducenti', USER_CATEGORY_PALETTE['conducente']),
    ('feriti_trasportati', 'Feriti trasportati', USER_CATEGORY_PALETTE['trasportato']),
    ('feriti_pedoni', 'Feriti pedoni', USER_CATEGORY_PALETTE['pedone']),
]:
    ax.plot(totali['anno'], totali[col], marker='o', linewidth=2, label=label, color=color)
ax.set_title('Feriti per categoria di utente')
ax.set_xlabel('Anno')
ax.set_ylabel('Feriti')
ax.set_xticks(anni)
ax.set_xticklabels(anni, rotation=45, ha='right')
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(loc='upper right')
plt.tight_layout()
plt.show()

_save_all_figures('cell_16_Analisi Temporale: Feriti Conducenti, Feriti Trasportati e Feriti Pedoni')

long_feriti_no_residui = df_long[(df_long['tipo_riga'].eq('causa_specifica')) & (df_long['categoria_utente_colpito']!='totale')].copy()
long_feriti_no_residui = long_feriti_no_residui[~long_feriti_no_residui['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)]
cat_year_feriti_no_residui = long_feriti_no_residui.groupby(['anno','categoria_utente_colpito'], as_index=False)['feriti'].sum()

anni = sorted(cat_year_feriti_no_residui['anno'].astype(int).unique())
fig, ax = plt.subplots(figsize=(14, 5.5))
sns.lineplot(
    data=cat_year_feriti_no_residui,
    x='anno',
    y='feriti',
    hue='categoria_utente_colpito',
    hue_order=['conducente', 'trasportato', 'pedone'],
    marker='o',
    palette=USER_CATEGORY_PALETTE,
    ax=ax,
)
ax.set_title('Feriti per categoria di utente, senza residuali')
ax.set_xlabel('Anno')
ax.set_ylabel('Feriti')
ax.set_xticks(anni)
ax.set_xticklabels(anni, rotation=45, ha='right')
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(title='Categoria utente colpito', loc='upper right')
plt.tight_layout()
plt.show()

_save_named_figures('02prime_feriti_per_categoria_senza_residuali')

# %% [markdown] cell 17
# Analisi Temporale: Morti Conducenti, Morti Trasportati e Morti Pedoni

# %% cell 18
long_core = df_long[(df_long['tipo_riga'].eq('causa_specifica')) & (df_long['categoria_utente_colpito']!='totale')].copy()
# Manteniamo anche le cause residuali per rendere il trend coerente con il totale annuale.
cat_year = long_core.groupby(['anno','categoria_utente_colpito'], as_index=False)['morti'].sum()
display(cat_year.pivot(index='anno', columns='categoria_utente_colpito', values='morti'))

anni = sorted(cat_year['anno'].astype(int).unique())
fig, ax = plt.subplots(figsize=(14, 5.5))
if sns is not None:
    sns.lineplot(
        data=cat_year,
        x='anno',
        y='morti',
        hue='categoria_utente_colpito',
        hue_order=['conducente', 'trasportato', 'pedone'],
        marker='o',
        palette=USER_CATEGORY_PALETTE,
        ax=ax,
    )
else:
    for categoria, group in cat_year.groupby('categoria_utente_colpito'):
        ax.plot(group['anno'], group['morti'], marker='o', linewidth=2, label=categoria, color=USER_CATEGORY_PALETTE.get(categoria))
ax.set_title('Morti per categoria di utente colpito')
ax.set_xlabel('Anno')
ax.set_ylabel('Morti')
ax.set_xticks(anni)
ax.set_xticklabels(anni, rotation=45, ha='right')
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(title='Categoria utente colpito', loc='upper right')
plt.tight_layout()
plt.show()

_save_all_figures('cell_18_Analisi Temporale: Morti Conducenti, Morti Trasportati e Morti Pedoni')

long_core_no_residui = long_core[~long_core['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)]
cat_year_no_residui = long_core_no_residui.groupby(['anno','categoria_utente_colpito'], as_index=False)['morti'].sum()

anni = sorted(cat_year_no_residui['anno'].astype(int).unique())
fig, ax = plt.subplots(figsize=(14, 5.5))
sns.lineplot(
    data=cat_year_no_residui,
    x='anno',
    y='morti',
    hue='categoria_utente_colpito',
    hue_order=['conducente', 'trasportato', 'pedone'],
    marker='o',
    palette=USER_CATEGORY_PALETTE,
    ax=ax,
)
ax.set_title('Morti per categoria di utente colpito, senza residuali')
ax.set_xlabel('Anno')
ax.set_ylabel('Morti')
ax.set_xticks(anni)
ax.set_xticklabels(anni, rotation=45, ha='right')
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(title='Categoria utente colpito', loc='upper right')
plt.tight_layout()
plt.show()

_save_named_figures('03prime_morti_per_categoria_senza_residuali')

# %% [markdown] cell 19
# ## 4. Cause principali: frequenza e gravita
#
# Una causa puo essere prioritaria perche genera molti incidenti, oppure perche ha pochi incidenti ma una mortalita alta. Per questo calcoliamo entrambi i ranking.

# %% [markdown] cell 20
# ## 4.1 Cause; Ranking Statico

# %% [markdown] cell 21
# Mortalità pool è il Tasso Aggregato, molto piu utile quando aggrego più anni

# %% [markdown] cell 22
# *"Al fine di identificare i pattern di rischio senza subire le distorsioni tipiche dei piccoli campioni (micro-cause con pochissimi eventi che generano tassi di mortalità artificialmente vicini a 1000), si è optato per due strategie metodologiche:Il calcolo della mortalita_pool, che aggrega l'intera massa di morti e incidenti del periodo prima di calcolare il tasso, fungendo da media ponderata implicita.Il filtraggio del ranking di letalità attraverso la rimozione del primo quartile delle distribuzioni degli incidenti ($Q_1$), escludendo le code della distribuzione ed evidenziando la pericolosità intrinseca delle sole cause statisticamente rilevanti."*

# %% cell 23
cause = df[df['tipo_riga'].eq('causa_specifica')].copy()
# Escludo righe residuali solo per alcuni ranking interpretativi; tenerle per audit e possibile analisi separata.
residuali = cause['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)
cause_core = cause[~residuali].copy()
CAUSE_PALETTE = _make_category_palette(cause_core['causa'])

ranking = (cause_core.groupby('causa', as_index=False)
           .agg(incidenti=('incidenti','sum'), morti=('morti_totale','sum'), feriti=('feriti_totale','sum'),
                mortalita_media=('mortalita_per_1000_incidenti','mean'), anni_presenti=('anno','nunique'))
           .assign(mortalita_pool=lambda x: x['morti'] / x['incidenti'].replace(0,np.nan) * 1000)
           .sort_values('incidenti', ascending=False))

display(ranking.head(15))
display(ranking.sort_values('morti', ascending=False).head(15))
display(ranking[ranking['incidenti'] >= ranking['incidenti'].quantile(.25)].sort_values('mortalita_pool', ascending=False).head(15))

#ranking per incidenti
#ranking per morti
#ranking per mortalità (solo cause con almeno 25% degli incidenti)

_save_all_figures('cell_23_*"Al fine di identificare i pattern di rischio senza subire le distorsioni tipiche dei piccoli campioni (micro-cause con pochissimi eventi che generano tassi di mortalità artificialmente vicini a 1000), si è optato per due strategie metodologiche:Il calcolo della mortalita_pool, che aggrega l\'intera massa di morti e incidenti del periodo prima di calcolare il tasso, fungendo da media ponderata implicita.Il filtraggio del ranking di letalità attraverso la rimozione del primo quartile delle distribuzioni degli incidenti ($Q_1$), escludendo le code della distribuzione ed evidenziando la pericolosità intrinseca delle sole cause statisticamente rilevanti."*')

# %% cell 24
# 1. Estrarre i dati per i primi due grafici (senza filtri di soglia minima)
top_inc = ranking.nlargest(12, 'incidenti').sort_values('incidenti')
top_dead = ranking.nlargest(12, 'morti').sort_values('morti')

# 2. Applicare il filtro del primo quartile (25%) sugli incidenti SOLO per il ranking di mortalità
soglia_25 = ranking['incidenti'].quantile(.25)
ranking_filtrato_mortalita = ranking[ranking['incidenti'] >= soglia_25]

# 3. Estrarre le 12 cause con più mortalità dal dataset pulito dal rumore statistico
top_mortalita = ranking_filtrato_mortalita.nlargest(12, 'mortalita_pool').sort_values('mortalita_pool')

# 4. Generazione dei tre grafici affiancati
fig, axes = plt.subplots(1, 3, figsize=(24, 8)) # Aumentata leggermente l'altezza a 8 per far respirare i testi delle cause

# Grafico 1: Incidenti (Colore Blu/Azzurro)
axes[0].barh(top_inc['causa'], top_inc['incidenti'], color='#4c72b0')
axes[0].set_title('Top 12 Cause per Numero di Incidenti\n(Somma 2007-2024)', fontsize=12, fontweight='bold')
axes[0].grid(axis='x', linestyle='--', alpha=0.5)

# Grafico 2: Morti (Colore Rosso/Arancio)
axes[1].barh(top_dead['causa'], top_dead['morti'], color='#c44e52')
axes[1].set_title('Top 12 Cause per Numero di Morti\n(Somma 2007-2024)', fontsize=12, fontweight='bold')
axes[1].grid(axis='x', linestyle='--', alpha=0.5)

# Grafico 3: Mortalità Pool Filtrata (Colore Viola)
axes[2].barh(top_mortalita['causa'], top_mortalita['mortalita_pool'], color='#8172b3')
axes[2].set_title('Top 12 Cause per Mortalità Pool\n(Solo cause con incidenti >= 25° percentile)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Morti ogni 1.000 incidenti')
axes[2].grid(axis='x', linestyle='--', alpha=0.5)

# Ottimizzazione del layout per evitare che i nomi lunghi delle cause si sovrappongano o vengano tagliati
plt.tight_layout()
plt.show()

_save_all_figures('cell_24_*"Al fine di identificare i pattern di rischio senza subire le distorsioni tipiche dei piccoli campioni (micro-cause con pochissimi eventi che generano tassi di mortalità artificialmente vicini a 1000), si è optato per due strategie metodologiche:Il calcolo della mortalita_pool, che aggrega l\'intera massa di morti e incidenti del periodo prima di calcolare il tasso, fungendo da media ponderata implicita.Il filtraggio del ranking di letalità attraverso la rimozione del primo quartile delle distribuzioni degli incidenti ($Q_1$), escludendo le code della distribuzione ed evidenziando la pericolosità intrinseca delle sole cause statisticamente rilevanti."*')

# %% [markdown] cell 25
# ## 4.2 Cause; Ranking annuale

# %% cell 26
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================================================
# 1. CALCOLO DEI TREND STORICI (Aggregazione annuale corretta)
# =====================================================================
trend_annuale = (cause_core.groupby(['causa', 'anno'], as_index=False)
                 .agg(incidenti=('incidenti', 'sum'), 
                      morti=('morti_totale', 'sum')))

# Chiamiamo la variabile con il suo vero nome annuale, non più "pool"
trend_annuale['mortalita_annuale'] = (trend_annuale['morti'] / 
                                      trend_annuale['incidenti'].replace(0, np.nan) * 1000)

anni_esatti = sorted(trend_annuale['anno'].unique())


# =====================================================================
# 2. SELEZIONE DELLE TOP 5 CON FILTRO DI CONTINUITÀ STORICA
# =====================================================================
top_5_incidenti = ranking.nlargest(5, 'incidenti')['causa'].tolist()
top_5_morti = ranking.sort_values('morti', ascending=False).head(5)['causa'].tolist()

# PER LA LETALITÀ: Applichiamo il doppio filtro (Volume minimo E continuità nel tempo)
soglia_25 = ranking['incidenti'].quantile(.25)
ranking_filtrato = ranking[ranking['incidenti'] >= soglia_25]

# ESCLUSIONE DELLE CAUSE SPARITE: Devono essere presenti in almeno 15 anni su 18
ranking_continuita = ranking_filtrato[ranking_filtrato['anni_presenti'] >= 15]
top_5_mortalita = ranking_continuita.sort_values('mortalita_pool', ascending=False).head(5)['causa'].tolist()


# =====================================================================
# 3. FILTRAGGIO DATASET PER IL PLOTTING
# =====================================================================
df_plot_inc = trend_annuale[trend_annuale['causa'].isin(top_5_incidenti)]
df_plot_morti = trend_annuale[trend_annuale['causa'].isin(top_5_morti)]
df_plot_pool = trend_annuale[trend_annuale['causa'].isin(top_5_mortalita)]


# =====================================================================
# 4. PLOTTING GENERALE AGGIORNATO
# =====================================================================
fig, axes = plt.subplots(1, 3, figsize=(26, 10))

# --- GRAFICO 1: INCIDENTI ---
sns.lineplot(data=df_plot_inc, x='anno', y='incidenti', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[0], linewidth=2.5)
axes[0].set_title('Evoluzione delle 5 Cause\ncon più INCIDENTI globali', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Anno')
axes[0].set_ylabel('Numero di Incidenti')
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].set_xticks(anni_esatti)
axes[0].set_xticklabels(anni_esatti, rotation=45)
axes[0].legend(title='Top Cause Incidenti', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 2: MORTI ---
sns.lineplot(data=df_plot_morti, x='anno', y='morti', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[1], linewidth=2.5)
axes[1].set_title('Evoluzione delle 5 Cause\ncon più MORTI globali', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Anno')
axes[1].set_ylabel('Numero di Morti')
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].set_xticks(anni_esatti)
axes[1].set_xticklabels(anni_esatti, rotation=45)
axes[1].legend(title='Top Cause Morti', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 3: MORTALITÀ ANNUALE (PULITO E CONTINUO) ---
# Usiamo la nuova variabile 'mortalita_annuale' coerente con la tua intuizione
sns.lineplot(data=df_plot_pool, x='anno', y='mortalita_annuale', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[2], linewidth=2.5)
axes[2].set_title('Evoluzione della Pericolosità delle 5 Cause\npiù LETALI (Presenti su tutta la serie)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Anno')
axes[2].set_ylabel('Morti ogni 1.000 incidenti (Tasso Annuale)')
axes[2].grid(True, linestyle='--', alpha=0.5)
axes[2].set_xticks(anni_esatti)
axes[2].set_xticklabels(anni_esatti, rotation=45)
axes[2].legend(title='Top Cause Letalità', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

plt.subplots_adjust(bottom=0.38)
plt.tight_layout()
plt.show()

_save_all_figures('cell_26_4.2 Cause; Ranking annuale')

# %% [markdown] cell 27
# # 5. Categorie di Utenti: conducenti, trasportati, pedoni

# %% [markdown] cell 28
# ## 5.1 Profili generali di Morte per anni delle categorie, senza cause

# %% [markdown] cell 29
# quota_x_pct rappresenta la percentuale di morti che quella categoria occupa sul totale dei morti

# %% cell 30
victim_cols = ['morti_conducenti','morti_trasportati','morti_pedoni']
victim_profile = (cause_core.groupby('causa')[victim_cols + ['morti_totale','incidenti']].sum()
                  .assign(quota_pedoni_pct=lambda x: x['morti_pedoni']/x['morti_totale'].replace(0,np.nan)*100,
                          quota_conducenti_pct=lambda x: x['morti_conducenti']/x['morti_totale'].replace(0,np.nan)*100,
                          quota_trasportati_pct=lambda x: x['morti_trasportati']/x['morti_totale'].replace(0,np.nan)*100)
                  .reset_index())
display(victim_profile.sort_values('morti_pedoni', ascending=False).head(15))

display(cat_year.head())

_save_all_figures('cell_30_quota_x_pct rappresenta la percentuale di morti che quella categoria occupa sul totale dei morti')

# %% [markdown] cell 31
# potrebbe essere indice di un'evoluzione della protezione interna delle vetture?

# %% [markdown] cell 32
# Nelle prossime scelte si analizzano feriti e morti assoluti, perdendo del dettaglio dei dati pool, ma focalizzandosi piu su quali cause danno piu feriti e morti in genreale piutttosto che quali sono le cause piu mortali o dannose per categoria, scelta operativa pratica

# %% [markdown] cell 33
# ## 5.2 Cause di Morti

# %% [markdown] cell 34
# ### 5.2.1 Top Cause di Morti, Conducenti/Trasportati/Pedoni

# %% cell 35
cause = df[df['tipo_riga'].eq('causa_specifica')].copy()
residuali = cause['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)
cause_core = cause[~residuali].copy()

# Raggruppamento per l'analisi statica
ranking = (cause_core.groupby('causa', as_index=False)
           .agg(morti_conducenti=('morti_conducenti','sum'), 
                morti_trasportati=('morti_trasportati','sum'), 
                morti_pedoni=('morti_pedoni','sum'),
                anni_presenti=('anno','nunique')))

print("--- TOP 15 MORTI CONDUCENTI ---")
display(ranking.sort_values('morti_conducenti', ascending=False).head(15))
print("\n--- TOP 15 MORTI TRASPORTATI ---")
display(ranking.sort_values('morti_trasportati', ascending=False).head(15))
print("\n--- TOP 15 MORTI PEDONI ---")
display(ranking.sort_values('morti_pedoni', ascending=False).head(15))

_save_all_figures('cell_35_5.2.1 Top Cause di Morti, Conducenti/Trasportati/Pedoni')

# %% [markdown] cell 36
# ### 5.2.2 Top Cause di Morti, Conducenti/Trasportati/Pedoni-Trend Annuale

# %% cell 37
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. CALCOLO DEI TREND STORICI ANNALI
trend_annuale = (cause_core.groupby(['causa', 'anno'], as_index=False)
                 .agg(morti_conducenti=('morti_conducenti', 'sum'), 
                      morti_trasportati=('morti_trasportati', 'sum'),
                      morti_pedoni=('morti_pedoni', 'sum')))

anni_esatti = sorted(trend_annuale['anno'].unique())

# 2. SELEZIONE DELLE TOP 5 INDIPENDENTI CON FILTRO DI VOLUME E CONTINUITÀ
# --- Conducenti ---
soglia_25_c = ranking['morti_conducenti'].quantile(.25)
ranking_filtrato_c = ranking[ranking['morti_conducenti'] >= soglia_25_c]
ranking_continuita_c = ranking_filtrato_c[ranking_filtrato_c['anni_presenti'] >= 15]
top_5_morti_conducenti = ranking_continuita_c.sort_values('morti_conducenti', ascending=False).head(5)['causa'].tolist()

# --- Trasportati ---
soglia_25_t = ranking['morti_trasportati'].quantile(.25)
ranking_filtrato_t = ranking[ranking['morti_trasportati'] >= soglia_25_t]
ranking_continuita_t = ranking_filtrato_t[ranking_filtrato_t['anni_presenti'] >= 15]
top_5_morti_trasportati = ranking_continuita_t.sort_values('morti_trasportati', ascending=False).head(5)['causa'].tolist()

# --- Pedoni ---
soglia_25_p = ranking['morti_pedoni'].quantile(.25)
ranking_filtrato_p = ranking[ranking['morti_pedoni'] >= soglia_25_p]
ranking_continuita_p = ranking_filtrato_p[ranking_filtrato_p['anni_presenti'] >= 15]
top_5_morti_pedoni = ranking_continuita_p.sort_values('morti_pedoni', ascending=False).head(5)['causa'].tolist()


# 3. FILTRAGGIO DATASET PER IL PLOTTING
df_plot_morti_conducenti = trend_annuale[trend_annuale['causa'].isin(top_5_morti_conducenti)]
df_plot_morti_trasportati = trend_annuale[trend_annuale['causa'].isin(top_5_morti_trasportati)]
df_plot_morti_pedoni = trend_annuale[trend_annuale['causa'].isin(top_5_morti_pedoni)]


# 4. PLOTTING GENERALE AGGIORNATO (3 Grafici a Linee Affiancati)
fig, axes = plt.subplots(1, 3, figsize=(26, 11))

# --- GRAFICO 1: CONDUCENTI ---
sns.lineplot(data=df_plot_morti_conducenti, x='anno', y='morti_conducenti', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[0], linewidth=2.5)
axes[0].set_title('Evoluzione delle 5 Cause\ncon più Morti Conducenti', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Anno')
axes[0].set_ylabel('Numero di Morti Conducenti')
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].set_xticks(anni_esatti)
axes[0].set_xticklabels(anni_esatti, rotation=45)
axes[0].legend(title='Top Cause Morti Conducenti', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 2: TRASPORTATI ---
sns.lineplot(data=df_plot_morti_trasportati, x='anno', y='morti_trasportati', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[1], linewidth=2.5)
axes[1].set_title('Evoluzione delle 5 Cause\ncon più Morti Trasportati', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Anno')
axes[1].set_ylabel('Numero di Morti Trasportati')
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].set_xticks(anni_esatti)
axes[1].set_xticklabels(anni_esatti, rotation=45)
axes[1].legend(title='Top Cause Morti Trasportati', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 3: PEDONI (Corretto df_plot_morti_pedoni) ---
sns.lineplot(data=df_plot_morti_pedoni, x='anno', y='morti_pedoni', hue='causa', marker='o', palette=CAUSE_PALETTE, ax=axes[2], linewidth=2.5)
axes[2].set_title('Evoluzione delle 5 Cause\ncon più Morti Pedoni', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Anno')
axes[2].set_ylabel('Numero di Morti Pedoni')
axes[2].grid(True, linestyle='--', alpha=0.5)
axes[2].set_xticks(anni_esatti)
axes[2].set_xticklabels(anni_esatti, rotation=45)
axes[2].legend(title='Top Cause Morti Pedoni', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

plt.subplots_adjust(bottom=0.38)
plt.tight_layout()
plt.show()

_save_all_figures('cell_37_5.2.2 Top Cause di Morti, Conducenti/Trasportati/Pedoni-Trend Annuale')

# %% [markdown] cell 38
# ## 5.3 Cause di Feriti

# %% [markdown] cell 39
# ### 5.3.1 Top Cause per anno di Feriti, Conducenti/Trasportati/Pedoni

# %% cell 40
cause = df[df['tipo_riga'].eq('causa_specifica')].copy()
residuali = cause['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)
cause_core = cause[~residuali].copy()

# Raggruppamento per l'analisi statica
ranking = (cause_core.groupby('causa', as_index=False)
           .agg(feriti_conducenti=('feriti_conducenti','sum'), 
                feriti_trasportati=('feriti_trasportati','sum'), 
                feriti_pedoni=('feriti_pedoni','sum'),
                anni_presenti=('anno','nunique')))

print("--- TOP 15 FERITI CONDUCENTI ---")
display(ranking.sort_values('feriti_conducenti', ascending=False).head(15))
print("\n--- TOP 15 FERITI TRASPORTATI ---")
display(ranking.sort_values('feriti_trasportati', ascending=False).head(15))
print("\n--- TOP 15 FERITI PEDONI ---")
display(ranking.sort_values('feriti_pedoni', ascending=False).head(15))

_save_all_figures('cell_40_5.3.1 Top Cause per anno di Feriti, Conducenti/Trasportati/Pedoni')

# %% [markdown] cell 41
# ### 5.3.2 Top Cause per anno di Feriti, Conducenti/Trasportati/Pedoni-Trend Annuale

# %% cell 42
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. CALCOLO DEI TREND STORICI ANNALI
trend_annuale = (cause_core.groupby(['causa', 'anno'], as_index=False)
                 .agg(incidenti=('incidenti', 'sum'),
                      feriti_conducenti=('feriti_conducenti', 'sum'), 
                      feriti_trasportati=('feriti_trasportati', 'sum'),
                      feriti_pedoni=('feriti_pedoni', 'sum')))

trend_annuale['tasso_feriti_conducenti'] = (trend_annuale['feriti_conducenti'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)
trend_annuale['tasso_feriti_trasportati'] = (trend_annuale['feriti_trasportati'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)
trend_annuale['tasso_feriti_pedoni'] = (trend_annuale['feriti_pedoni'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)

anni_esatti = sorted(trend_annuale['anno'].unique())

# 2. SELEZIONE DELLE TOP 5 INDIPENDENTI CON FILTRO DI VOLUME E CONTINUITÀ
# --- Conducenti ---
soglia_25_c = ranking['feriti_conducenti'].quantile(.25)
ranking_filtrato_c = ranking[ranking['feriti_conducenti'] >= soglia_25_c]
ranking_continuita_c = ranking_filtrato_c[ranking_filtrato_c['anni_presenti'] >= 15]
top_5_feriti_conducenti = ranking_continuita_c.sort_values('feriti_conducenti', ascending=False).head(5)['causa'].tolist()

# --- Trasportati ---
soglia_25_t = ranking['feriti_trasportati'].quantile(.25)
ranking_filtrato_t = ranking[ranking['feriti_trasportati'] >= soglia_25_t]
ranking_continuita_t = ranking_filtrato_t[ranking_filtrato_t['anni_presenti'] >= 15]
top_5_feriti_trasportati = ranking_continuita_t.sort_values('feriti_trasportati', ascending=False).head(5)['causa'].tolist()

# --- Pedoni ---
soglia_25_p = ranking['feriti_pedoni'].quantile(.25)
ranking_filtrato_p = ranking[ranking['feriti_pedoni'] >= soglia_25_p]
ranking_continuita_p = ranking_filtrato_p[ranking_filtrato_p['anni_presenti'] >= 15]
top_5_feriti_pedoni = ranking_continuita_p.sort_values('feriti_pedoni', ascending=False).head(5)['causa'].tolist()

# 3. FILTRAGGIO DATASET PER IL PLOTTING
df_plot_feriti_conducenti = trend_annuale[trend_annuale['causa'].isin(top_5_feriti_conducenti)]
df_plot_feriti_trasportati = trend_annuale[trend_annuale['causa'].isin(top_5_feriti_trasportati)]
df_plot_feriti_pedoni = trend_annuale[trend_annuale['causa'].isin(top_5_feriti_pedoni)]


# 4. PLOTTING GENERALE AGGIORNATO (3 Grafici a Linee Affiancati)
fig, axes = plt.subplots(1, 3, figsize=(26, 11))

# --- GRAFICO 1: CONDUCENTI ---
sns.lineplot(data=df_plot_feriti_conducenti, x='anno', y='tasso_feriti_conducenti', hue='causa', hue_order=top_5_feriti_conducenti, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_feriti_conducenti}, ax=axes[0], linewidth=2.5)
axes[0].set_title('Tasso di Feriti delle 5 Cause principali\n(Conducenti Feriti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Anno')
axes[0].set_ylabel('Feriti Conducenti ogni 1.000 incidenti')
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].set_xticks(anni_esatti)
axes[0].set_xticklabels(anni_esatti, rotation=45)
axes[0].legend(title='Top Cause Feriti Conducenti', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)
# --- GRAFICO 2: TRASPORTATI ---
sns.lineplot(data=df_plot_feriti_trasportati, x='anno', y='tasso_feriti_trasportati', hue='causa', hue_order=top_5_feriti_trasportati, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_feriti_trasportati}, ax=axes[1], linewidth=2.5)
axes[1].set_title('Tasso di Feriti delle 5 Cause principali\n(Trasportati Feriti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Anno')
axes[1].set_ylabel('Feriti Trasportati ogni 1.000 incidenti')
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].set_xticks(anni_esatti)
axes[1].set_xticklabels(anni_esatti, rotation=45)
axes[1].legend(title='Top Cause Feriti Trasportati', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 3: PEDONI (Corretto df_plot_feriti_pedoni) ---
sns.lineplot(data=df_plot_feriti_pedoni, x='anno', y='tasso_feriti_pedoni', hue='causa', hue_order=top_5_feriti_pedoni, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_feriti_pedoni}, ax=axes[2], linewidth=2.5)
axes[2].set_title('Tasso di Feriti delle 5 Cause principali\n(Pedoni Feriti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Anno')
axes[2].set_ylabel('Feriti Pedoni ogni 1.000 incidenti')
axes[2].grid(True, linestyle='--', alpha=0.5)
axes[2].set_xticks(anni_esatti)
axes[2].set_xticklabels(anni_esatti, rotation=45)
axes[2].legend(title='Top Cause Feriti Pedoni', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)
plt.subplots_adjust(bottom=0.38)
plt.tight_layout()
plt.show()

_save_all_figures('cell_42_5.3.2 Top Cause per anno di Feriti, Conducenti/Trasportati/Pedoni-Trend Annuale')

# %% [markdown] cell 43
# ### 5.4 Approfondimento, Mortalità delle Cause

# %% [markdown] cell 44
# Una causa con un alto numero di morti per una categoria rappresenta sicuramente un punto di interesse politico, tuttavia, dal momento in cui l'aumento o la diminuzione del numero di morti per categoria attribuibile ad una causa, non comporta un'aumento o diminuzione della Mortalità della causa, ma potrebbe essere dovuto ad un aumento o diminuzione del numero di incidenti per quella causa in generale, sono stati calcolati i tassi di mortalità di ogni causa divisi per categoria.

# %% cell 45
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================================================
# BLOCCO 1: RANKING STATICO GLOBALE CON AGGREGAZIONE INCIDENTI (CORRETTO)
# =====================================================================
cause = df[df['tipo_riga'].eq('causa_specifica')].copy()
residuali = cause['causa'].str.contains('Altre circostanze|imprecisate|concomitanti', case=False, na=False)
cause_core = cause[~residuali].copy()

ranking = (cause_core.groupby('causa', as_index=False)
           .agg(incidenti=('incidenti', 'sum'), # <--- AGGIUNTO QUI: serve come base stabile per i filtri
                morti_conducenti=('morti_conducenti','sum'), 
                morti_trasportati=('morti_trasportati','sum'), 
                morti_pedoni=('morti_pedoni','sum'),
                anni_presenti=('anno','nunique')))


# =====================================================================
# 1. CALCOLO DEI TREND STORICI ANNALI
# =====================================================================
trend_annuale = (cause_core.groupby(['causa', 'anno'], as_index=False)
                 .agg(incidenti=('incidenti', 'sum'), 
                      morti_conducenti=('morti_conducenti', 'sum'), 
                      morti_trasportati=('morti_trasportati', 'sum'),
                      morti_pedoni=('morti_pedoni', 'sum')))

# Calcolo dei tassi specifici purificati
trend_annuale['tasso_conducenti'] = (trend_annuale['morti_conducenti'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)
trend_annuale['tasso_trasportati'] = (trend_annuale['morti_trasportati'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)
trend_annuale['tasso_pedoni'] = (trend_annuale['morti_pedoni'] / trend_annuale['incidenti'].replace(0, np.nan) * 1000)

anni_esatti = sorted(trend_annuale['anno'].unique())


# =====================================================================
# 2. SELEZIONE DELLE TOP 5 CON SOGLIA UNIFICATA SUL VOLUME DI INCIDENTI
# =====================================================================
# Usiamo il 25° percentile degli INCIDENTI TOTALI come filtro di stabilità statistica universale
soglia_volume = ranking['incidenti'].quantile(.25)
ranking_stabilizzato = ranking[ranking['incidenti'] >= soglia_volume]

# Applichiamo la continuità storica (almeno 15 anni su 18)
ranking_continuita = ranking_stabilizzato[ranking_stabilizzato['anni_presenti'] >= 15]

# Ora estraiamo le top 5 specifiche per ogni categoria di utente
top_5_morti_conducenti = ranking_continuita.sort_values('morti_conducenti', ascending=False).head(5)['causa'].tolist()
top_5_morti_trasportati = ranking_continuita.sort_values('morti_trasportati', ascending=False).head(5)['causa'].tolist()
top_5_morti_pedoni = ranking_continuita.sort_values('morti_pedoni', ascending=False).head(5)['causa'].tolist()


# =====================================================================
# 3. FILTRAGGIO DATASET PER IL PLOTTING
# =====================================================================
df_plot_morti_conducenti = trend_annuale[trend_annuale['causa'].isin(top_5_morti_conducenti)]
df_plot_morti_trasportati = trend_annuale[trend_annuale['causa'].isin(top_5_morti_trasportati)]
df_plot_morti_pedoni = trend_annuale[trend_annuale['causa'].isin(top_5_morti_pedoni)]


# =====================================================================
# 4. PLOTTING GENERALE DEI TASSI (3 Grafici a Linee Affiancati)
# =====================================================================
fig, axes = plt.subplots(1, 3, figsize=(26, 11))

# --- GRAFICO 1: CONDUCENTI ---
sns.lineplot(data=df_plot_morti_conducenti, x='anno', y='tasso_conducenti', hue='causa', hue_order=top_5_morti_conducenti, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_morti_conducenti}, ax=axes[0], linewidth=2.5)
axes[0].set_title('Tasso di Letalità delle 5 Cause principali\n(Conducenti Morti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Anno')
axes[0].set_ylabel('Tasso di Mortalità Specifico')
axes[0].grid(True, linestyle='--', alpha=0.5)
axes[0].set_xticks(anni_esatti)
axes[0].set_xticklabels(anni_esatti, rotation=45)
axes[0].legend(title='Top Cause Conducenti', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 2: TRASPORTATI ---
sns.lineplot(data=df_plot_morti_trasportati, x='anno', y='tasso_trasportati', hue='causa', hue_order=top_5_morti_trasportati, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_morti_trasportati}, ax=axes[1], linewidth=2.5)
axes[1].set_title('Tasso di Letalità delle 5 Cause principali\n(Trasportati Morti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Anno')
axes[1].set_ylabel('Tasso di Mortalità Specifico')
axes[1].grid(True, linestyle='--', alpha=0.5)
axes[1].set_xticks(anni_esatti)
axes[1].set_xticklabels(anni_esatti, rotation=45)
axes[1].legend(title='Top Cause Trasportati', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

# --- GRAFICO 3: PEDONI ---
sns.lineplot(data=df_plot_morti_pedoni, x='anno', y='tasso_pedoni', hue='causa', hue_order=top_5_morti_pedoni, marker='o', palette={causa: CAUSE_PALETTE[causa] for causa in top_5_morti_pedoni}, ax=axes[2], linewidth=2.5)
axes[2].set_title('Tasso di Letalità delle 5 Cause principali\n(Pedoni Morti ogni 1.000 incidenti)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Anno')
axes[2].set_ylabel('Tasso di Mortalità Specifico')
axes[2].grid(True, linestyle='--', alpha=0.5)
axes[2].set_xticks(anni_esatti)
axes[2].set_xticklabels(anni_esatti, rotation=45)
axes[2].legend(title='Top Cause Pedoni', bbox_to_anchor=(0.5, -0.18), loc='upper center', fontsize=9)

plt.subplots_adjust(bottom=0.38)
plt.tight_layout()
plt.show()

_save_named_figures('04prime_tasso_letalita_top_cause_per_categoria')

# %% [markdown] cell 46
# # 6. Correlazioni tra cause
#
# La vecchia correlazione tra indicatori era poco informativa: confrontava metriche costruite
# dagli stessi conteggi e quindi produceva relazioni quasi ovvie. Qui confrontiamo le cause
# tra loro usando la quota annuale di morti, dopo aver rimosso il trend generale della
# mortalita stradale nazionale. La matrice resta esplorativa: indica andamenti simili od
# opposti, non relazioni causali.

# %% cell 47
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform


def _short_cause_label(cause_name):
    aliases = {
        'Manovrava in retrocessione o conversione': 'Retromarcia/conversione',
        'Non dava la precedenza al pedone': 'Precedenza pedoni',
        'Procedeva con guida distratta': 'Guida distratta',
        'Svoltava a sinistra irregolarmente': 'Svolta sinistra irregolare',
        'con eccesso di velocità': 'Velocita',
        'contromano': 'Contromano',
        'Procedeva non in prossimità del margine destro': 'Margine destro',
        'per immettersi nel flusso della circolazione': 'Immissione nel flusso',
        'per svoltare a sinistra': 'Svolta sinistra accesso',
        'senza dare la precedenza al veicolo proveniente da destra': 'Precedenza da destra',
        'senza mantenere la distanza di sicurezza': 'Distanza sicurezza',
        'senza rispettare il segnale di dare precedenza': 'Dare precedenza',
        "senza rispettare le segnalazioni semaforiche o dell'agente": 'Semaforo/agente',
        'senza rispettare lo stop': 'Stop',
        'Ostacolo accidentale': 'Ostacolo accidentale',
        'Attraversava la strada irregolarmente': 'Pedone attraversamento irregolare',
    }
    for pattern, alias in aliases.items():
        if pattern in cause_name:
            return alias
    return re.sub(r'^\[[^\]]+\]\s*', '', cause_name)[:32]


cause_year = (cause_core.groupby(['anno', 'causa'], as_index=False)
              .agg(incidenti=('incidenti', 'sum'),
                   morti=('morti_totale', 'sum')))
annual_totals = (df[df['tipo_riga'].eq('totale')]
                 [['anno', 'morti_totale', 'mortalita_per_1000_incidenti']]
                 .rename(columns={
                     'morti_totale': 'morti_anno_totale',
                     'mortalita_per_1000_incidenti': 'mortalita_nazionale'
                 }))
cause_year = cause_year.merge(annual_totals, on='anno', how='left')
cause_year['quota_morti_anno_pct'] = (
    cause_year['morti'] / cause_year['morti_anno_totale'].replace(0, np.nan) * 100
)

cause_summary = (cause_year.groupby('causa', as_index=False)
                 .agg(incidenti=('incidenti', 'sum'),
                      morti=('morti', 'sum'),
                      anni_presenti=('anno', 'nunique')))
top_cause_corr = cause_summary[
    cause_summary['anni_presenti'] >= 15
].nlargest(15, 'morti')['causa']

cause_matrix = (cause_year[cause_year['causa'].isin(top_cause_corr)]
                .pivot(index='anno', columns='causa', values='quota_morti_anno_pct')
                .sort_index())
trend = annual_totals.set_index('anno').loc[cause_matrix.index, 'mortalita_nazionale']
trend_x = np.column_stack([np.ones(len(trend)), trend.to_numpy(dtype=float)])

detrended_matrix = cause_matrix.copy()
for col in detrended_matrix.columns:
    valid = detrended_matrix[col].notna() & np.isfinite(trend)
    if valid.sum() >= 8:
        beta = np.linalg.lstsq(
            trend_x[valid.to_numpy()],
            detrended_matrix.loc[valid, col].to_numpy(dtype=float),
            rcond=None,
        )[0]
        detrended_matrix.loc[valid, col] = (
            detrended_matrix.loc[valid, col] - trend_x[valid.to_numpy()] @ beta
        )

cause_corr = detrended_matrix.corr(method='spearman', min_periods=8)
cause_corr.index = [_short_cause_label(c) for c in cause_corr.index]
cause_corr.columns = [_short_cause_label(c) for c in cause_corr.columns]

if sns is not None:
    corr_for_clustering = cause_corr.fillna(0).clip(-1, 1)
    distance = (1 - corr_for_clustering.abs()).to_numpy(copy=True)
    np.fill_diagonal(distance, 0)
    row_linkage = linkage(squareform(distance, checks=False), method='average')
    annotation = cause_corr.where(cause_corr.abs() >= .5).round(2).astype(object)
    annotation = annotation.where(annotation.notna(), '').to_numpy(copy=True)
    np.fill_diagonal(annotation, '')

    grid = sns.clustermap(
        cause_corr,
        row_linkage=row_linkage,
        col_linkage=row_linkage,
        mask=np.eye(cause_corr.shape[0], dtype=bool),
        annot=annotation,
        fmt='',
        cmap='vlag',
        center=0,
        vmin=-1,
        vmax=1,
        linewidths=.4,
        figsize=(12, 10),
        cbar_kws={'label': 'Correlazione Spearman'},
    )
    grid.ax_heatmap.set_title('Cause correlate dopo rimozione del trend nazionale', pad=18)
    grid.ax_heatmap.set_xlabel('')
    grid.ax_heatmap.set_ylabel('')
    grid.ax_heatmap.set_xticklabels(grid.ax_heatmap.get_xticklabels(), rotation=45, ha='right')
    grid.ax_heatmap.set_yticklabels(grid.ax_heatmap.get_yticklabels(), rotation=0)
    plt.show()
else:
    display(cause_corr)

_save_all_figures('cell_47_6. Correlazioni tra cause')

# %% [markdown] cell 48
# Boxplot normale (Analisi outliers)

# %% [markdown] cell 49
# I boxplot sono stati costruiti sulle macrocause per avere piu osservazioni

# %% cell 50
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================================================
# ASSIGNMENT: Sostituisci 'df' con la tua vera variabile se ha un altro nome
df_analisi = df  # Es. df, df_completo, o cause_core
# =====================================================================

# Lista aggiornata con le tue 7 variabili
features_numeriche = [
    'incidenti', 'morti_totale', 'feriti_totale', 'mortalita_per_1000_incidenti',
    'morti_conducenti','morti_trasportati','morti_pedoni']

# Plot normale rimosso: la versione in scala logaritmica sotto è più leggibile per dati molto asimmetrici.

# %% [markdown] cell 51
# Boxplot con scala logaritmica

# %% cell 52
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# =====================================================================
# ASSIGNMENT: Sostituisci 'df' con la tua vera variabile se ha un altro nome
df_analisi = df  # Es. df, df_completo, o cause_core
# =====================================================================

# Lista aggiornata con le tue 7 variabili
features_numeriche = [
    'incidenti', 'morti_totale', 'feriti_totale', 'mortalita_per_1000_incidenti',
    'morti_conducenti','morti_trasportati','morti_pedoni']

# Configuriama una griglia 4x2 (8 slot totali per ospitare 7 grafici)
fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(16, 24))
axes = axes.flatten()

for i, col in enumerate(features_numeriche):
    
    # 1. Calcoliamo se la variabile ha valori coerenti con la scala log (maggiori di 0)
    # Se ci sono zeri (es. 0 morti), usiamo una scala "symlog" (symmetrical log) per non scassare il grafico
    min_val = df_analisi[col].min()
    
    # 2. Disegniamo il Boxplot
    sns.boxplot(
        data=df_analisi, 
        x=col, 
        y='macro_categoria',  # Aggiornato con il tuo nome colonna
        ax=axes[i], 
        palette='Set2',
        flierprops={'markerfacecolor':'red', 'marker':'o', 'markersize': 5, 'markeredgecolor':'none'}
    )
    
    # 3. APPLICAZIONE DELLA SCALA LOGARITMICA (Risolve lo schiacciamento)
    if min_val <= 0:
        axes[i].set_xscale('symlog', linthresh=1.0) # Gestisce logaritmi anche con lo zero assoluto
    else:
        axes[i].set_xscale('log')
        
    axes[i].set_title(f'Distribuzione (Scala Log) di: {col}', fontsize=12, fontweight='bold')
    axes[i].set_xlabel('')
    axes[i].set_ylabel('')
    
    # Pulizia grafica delle etichette a destra per non sovrapporsi
    if i % 2 != 0:
        axes[i].set_yticklabels([])

# Spegniamo l'8° grafico della griglia (visto che le variabili sono 7)
fig.delaxes(axes[-1])

plt.tight_layout()
plt.show()

_save_all_figures('cell_52_Boxplot con scala logaritmica')

# %% [markdown] cell 53
# No percentuali sulla scala log!

# %% [markdown] cell 54
# Perché la scala logaritmica NON dà una visualizzazione distorta, ma è quella GIUSTA?Capisco perfettamente il tuo dubbio: istintivamente pensiamo che modificare l'asse alteri la realtà dei dati. In statistica, però, è l'esatto contrario. Quando un dataset soffre di iper-asimmetria (come i dati ISTAT), la scala lineare distorce la nostra capacità di analisi, mentre la scala logaritmica la corregge.Ecco i motivi scientifici per cui la scala log è quella corretta per questo esame:1. Rispetta la natura moltiplicativa (e non additiva) dei fenomeni socialiNel tuo dataset ci sono cause microscopiche che fanno $1, 2, 5$ incidenti, e macro-cause che ne fanno $5.000$ o $10.000$.In scala lineare, la distanza visiva tra $1$ e $10$ incidenti è minuscola (un millimetro), mentre la distanza tra $5.000$ e $10.000$ è gigantesca (metà pagina).Ma pensa alla proporzione: passare da 1 a 10 incidenti significa un aumento del 1000% (un incremento di gravità pazzesco!). Passare da 5.000 a 10.000 è un raddoppio (100%).La scala logaritmica ragiona per ordini di grandezza (proporzioni): mette alla stessa distanza visiva i passaggi $1 \rightarrow 10$, $10 \rightarrow 100$, $100 \rightarrow 1.000$. Cattura l'intensità reale del rischio statistico, non solo il volume bruto.2. Permette di vedere le distribuzioni "nascoste"Nella scala lineare che mi hai mostrato nell'immagine, il 95% delle informazioni reali era compresso in un millimetro di spazio vicino allo zero. Tu vedevi solo "scatole microscopiche". Questo ti impediva di rispondere a domande fondamentali per il progetto, come:La macro-categoria A ha una varianza interna maggiore della macro-categoria B?Dov'è posizionata la mediana delle cause minori?La scala logaritmica funge da lente d'ingrandimento: dilata lo spazio vicino allo zero (mostrandoti finalmente la forma, i quartili e la vera dimensione delle scatole delle cause più piccole) e restringe lo spazio dei numeri giganti. Non stai inventando i dati, stai solo cambiando l'unita di misura dell'asse per poter leggere il grafico.3. Prepara la mente (e il report) ai modelli successiviMolti algoritmi statistici (e la stessa professoressa all'esame) sanno che i conteggi puri non sono distribuiti normalmente. Mostrare un boxplot in scala logaritmica è un'ottima mossa accademica. Dimostra che hai capito che il dataset è governato da una legge di potenza (poche cause fanno quasi tutto il totale) e giustifica fin da ora l'uso futuro di modelli robusti (come gli alberi o le foreste) che gestiscono nativamente queste disparità di scala senza rompersi.

# %% [markdown] cell 55
# Cosa fare?

# %% [markdown] cell 56
# Soluzione 1 (Trasformazione Logaritmica): Invece di usare i numeri assoluti (es. 10.000 incidenti), usi $\log(\text{incidenti} + 1)$. Il logaritmo "schiaccia" i valori giganti e avvicina gli outliers al resto dei dati.Soluzione 2 (Standardizzazione / Proporzioni): Lavori su percentuali o tassi (es. letalita_su_vittime_pct). Questo ridimensiona l'impatto del volume assoluto.Soluzione 3 (Metodi Robusti): Se calcoli la correlazione, usi Spearman invece di Pearson. Spearman guarda l'ordine di classifica (i ranghi), quindi se un valore è 1.000 o 1.000.000, per l'algoritmo sarà comunque semplicemente "il più grande", annullando l'effetto distorcente dell'outlier.

# %% cell 57
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================================
# ASSIGNMENT: Sostituisci 'tuo_dataframe' con la tua vera variabile
df_analisi = df  # Es. df, df_completo, o cause_core
# =====================================================================

# Selezioniamo le variabili chiave per non appesantire troppo il calcolo grafico
features_volumi_e_tassi = ['incidenti', 'morti_totale', 'feriti_totale', 'letalita_su_vittime_pct']

# Controlliamo che le colonne esistano nel dataset prima di plottare
features_presenti = [c for c in features_volumi_e_tassi if c in df_analisi.columns]

# Generiamo il pairplot includendo la variabile categorica come fattore di colore (hue)
# NOTA: kind='scatter' evita conflitti con le rette globali se i gruppi sono molto distorti
grid = sns.pairplot(
    data=df_analisi[features_presenti + ['macro_categoria']], 
    hue='macro_categoria', 
    palette='tab10',
    diag_kind='kde',
    plot_kws={'alpha': 0.7, 's': 40} # Trasparenza e dimensione dei punti ottimizzate
)

grid.fig.suptitle('Matrice Scatter Plot: Verifica delle Relazioni Lineari per Macro Causa', y=1.02, fontsize=14, fontweight='bold')
plt.show()

_save_all_figures('cell_57_Soluzione 1 (Trasformazione Logaritmica): Invece di usare i numeri assoluti (es. 10.000 incidenti), usi $\\log(\\text{incidenti} + 1)$. Il logaritmo "schiaccia" i valori giganti e avvicina gli outliers al resto dei dati.Soluzione 2 (Standardizzazione / Proporzioni): Lavori su percentuali o tassi (es. letalita_su_vittime_pct). Questo ridimensiona l\'impatto del volume assoluto.Soluzione 3 (Metodi Robusti): Se calcoli la correlazione, usi Spearman invece di Pearson. Spearman guarda l\'ordine di classifica (i ranghi), quindi se un valore è 1.000 o 1.000.000, per l\'algoritmo sarà comunque semplicemente "il più grande", annullando l\'effetto distorcente dell\'outlier.')

# %% [markdown] cell 58
# Scatterplot con assi logaritmici

# %% cell 59
# Genera il pairplot (usa il codice che abbiamo scritto prima)
grid = sns.pairplot(
    data=df_analisi[features_presenti + ['macro_categoria']], 
    hue='macro_categoria', 
    palette='tab10',
    diag_kind='kde'
)

# TRUCCO PER APRIRE IL MURO VERTICALE:
# Cicliamo su tutti i sotto-grafici della griglia e impostiamo la scala logaritmica sui conteggi
for ax in grid.axes.flat:
    if ax is not None:
        # Se l'asse X contiene una variabile di volume, la trasformiamo in logaritmo
        if ax.get_xlabel() in ['incidenti', 'morti_totale', 'feriti_totale']:
            ax.set_xscale('symlog', linthresh=1.0)
        # Se l'asse Y contiene una variabile di volume, la trasformiamo in logaritmo
        if ax.get_ylabel() in ['incidenti', 'morti_totale', 'feriti_totale']:
            ax.set_yscale('symlog', linthresh=1.0)

grid.fig.suptitle('Matrice Scatter Plot (Scala Log) per Macro Categoria', y=1.02, fontsize=14, fontweight='bold')
plt.show()

_save_all_figures('cell_59_Scatterplot con assi logaritmici')

# %% [markdown] cell 60
# # 7. Dimensionality reduction: PCA
#
# La PCA e utile per sintetizzare i profili delle cause: volume, mortalita, quota pedoni, quota conducenti e andamento nel tempo.

# %% [markdown] cell 61
# i dati hanno tutti la stessa unità di misura, pertanto non vi è necessità di standardizzazione(menziona)

# %% cell 62
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

pca_features = ['incidenti','morti_totale','feriti_totale','mortalita_per_1000_incidenti','letalita_su_vittime_pct',
                'quota_morti_pedoni_pct','quota_morti_conducenti_pct','quota_morti_trasportati_pct',
                'quota_incidenti_anno_pct','quota_morti_anno_pct']

cause_profile = (cause_core.groupby('causa', as_index=False)[pca_features]
                 .mean())
X = cause_profile[pca_features].replace([np.inf,-np.inf], np.nan).fillna(0)
X_scaled = StandardScaler().fit_transform(X)
pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(X_scaled)
pca_df = cause_profile[['causa']].copy()
pca_df['PC1'] = coords[:,0]
pca_df['PC2'] = coords[:,1]
print('Varianza spiegata:', pca.explained_variance_ratio_)
loadings = pd.DataFrame(pca.components_.T, index=pca_features, columns=['PC1','PC2']).sort_values('PC1', key=abs, ascending=False)
display(loadings)

plt.figure(figsize=(10,7))
plt.scatter(pca_df['PC1'], pca_df['PC2'], alpha=.75)
for _, r in pca_df.iterrows():
    if abs(r['PC1']) > pca_df['PC1'].abs().quantile(.85) or abs(r['PC2']) > pca_df['PC2'].abs().quantile(.85):
        plt.text(r['PC1'], r['PC2'], r['causa'][:35], fontsize=8)
plt.axhline(0, color='grey', lw=.8)
plt.axvline(0, color='grey', lw=.8)
plt.title('PCA dei profili medi delle cause')
plt.xlabel('PC1')
plt.ylabel('PC2')
plt.show()

_save_all_figures('cell_62_i dati hanno tutti la stessa unità di misura, pertanto non vi è necessità di standardizzazione(menziona)')

# %% [markdown] cell 63
# # 8. Clustering delle cause
#
# Il clustering raggruppa cause simili per frequenza, severita e profilo delle vittime. Questo aiuta a proporre interventi: alcune cause sono di massa, altre sono piu rare ma molto letali.

# %% [markdown] cell 64
# ## 8.1. Flip del Dataset per Clustering

# %% cell 65
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt
import seaborn as sns

# 2. Filtriamo solo le cause specifiche (escludiamo le righe macro_categoria e i totali)
df_micro = df[df['tipo_riga'] == 'causa_specifica'].copy()

# 3. Aggreghiamo facendo la SOMMA di tutti i 18 anni per ogni singola causa
# Questo ci serve per calcolare i tassi globali senza risentire di un singolo anno anomalo
df_sum = df_micro.groupby('causa').sum(numeric_only=True).reset_index()

# 4. Creiamo la matrice per il Clustering calcolando le 5 FEATURE RICHIESTE
df_cluster = pd.DataFrame()
df_cluster['causa'] = df_sum['causa']

#Feature 0, Macro di appartenenza
df_cluster['macro'] = (df['macro_categoria']) 

# Feature 1: Tasso di Mortalità Generale (per 1000 incidenti)
df_cluster['mortalita_rate'] = (df_sum['morti_totale'] / df_sum['incidenti']) * 1000

# Feature 2: Tasso di Ferimento Generale (per 1000 incidenti)
df_cluster['feriti_rate'] = (df_sum['feriti_totale'] / df_sum['incidenti']) * 1000

# Feature 3: Quota Morti Conducenti (sul totale dei morti di quella causa)
# Usiamo .fillna(0) nel caso una causa abbia fatto 0 morti totali in 18 anni
df_cluster['quota_morti_conducenti'] = (df_sum['morti_conducenti'] / df_sum['morti_totale']).fillna(0)

# Feature 4: Quota Morti Vulnerabili (Pedoni + Trasportati) sul totale dei morti della causa
df_cluster['quota_morti_vulnerabili'] = ((df_sum['morti_pedoni'] + df_sum['morti_trasportati']) / df_sum['morti_totale']).fillna(0)

# Feature 5 (La tua intuizione!): Volume Assoluto di Morti Generati (Media annuale nei 18 anni)
df_cluster['morti_medi_annui'] = df_sum['morti_totale'] / 18

# Impostiamo la causa come indice della tabella
df_cluster.set_index('causa', inplace=True)

_save_all_figures('cell_65_8.1. Flip del Dataset per Clustering')

# %% cell 66
display(df_cluster.head(100))
df_cluster.describe

_save_all_figures('cell_66_8.1. Flip del Dataset per Clustering')

# %% [markdown] cell 67
# ## 8.1. Pairplot filtrato per Macro Pre-Clustering

# %% cell 68
# Filtriamo le macro-categorie per un singolo anno (usando l'intero 2007, senza virgolette)
df_macro_2007 = df[(df['anno'] == 2007) & (df['tipo_riga'] == 'macro_categoria')]

# Estraiamo l'elenco delle macro-categorie uniche presenti nel dataset
macro_uniche = df_macro_2007['macro_categoria'].unique()
num_macro = len(macro_uniche)

print(f"Numero esatto di Macro-categorie: {num_macro}")
print("Elenco delle macro-categorie che verranno colorate:")
for i, macro in enumerate(macro_uniche, 1):
    print(f"{i}. {macro}")

_save_all_figures('cell_68_8.1. Pairplot filtrato per Macro Pre-Clustering')

# %% cell 69
import seaborn as sns
import matplotlib.pyplot as plt

# Scegliamo una palette robusta per 8 categorie (es. 'tab10')
palette_colori = "tab10"

# Creiamo il Pairplot delle 5 feature numeriche, colorando i punti in base alla macro_categoria
# Impostiamo diag_kind="kde" per vedere le curve di densità sui grafici diagonali
g = sns.pairplot(
    df_cluster, 
    hue="macro", 
    diag_kind="kde", 
    palette=palette_colori,
    plot_kws={'alpha': 0.7, 's': 50} # alpha rende i punti leggermente trasparenti per vedere le sovrapposizioni
)

# Regoliamo la legenda per fare in modo che non copra il grafico e sia leggibile
g._legend.set_title("Macro Categorie ISTAT")
plt.setp(g._legend.get_title(), fontsize=12, weight='bold')

# Spostiamo il titolo globale verso l'alto per non farlo sovrapporre ai grafici
plt.suptitle("Analisi di Coppia (Pairplot) Esplorativa colorata per Macro-Categoria ISTAT", y=1.02, fontsize=14, weight='bold')

plt.show()

_save_all_figures('cell_69_8.1. Pairplot filtrato per Macro Pre-Clustering')

# %% [markdown] cell 70
# ## 8.3. Clustering

# %% [markdown] cell 71
# Isolamento numeriche (drop macro)

# %% cell 72
from scipy.cluster.hierarchy import dendrogram, linkage, cut_tree, cophenet, fcluster
from scipy.spatial.distance import pdist, squareform, cdist
# Selezioniamo solo le 5 colonne numeriche, escludendo la macro_categoria testuale
features_numeriche = ['mortalita_rate', 'feriti_rate', 'quota_morti_conducenti', 'quota_morti_vulnerabili', 'morti_medi_annui']
X_scaled = StandardScaler().fit_transform(df_cluster[features_numeriche])

_save_all_figures('cell_72_Isolamento numeriche (drop macro)')

# %% [markdown] cell 73
# Clusters, No cut

# %% cell 74
# 2. Calcolo delle distanze e dei Linkage (Corretto)
X_dist = pdist(X_scaled, metric='euclidean')

Z_s = linkage(X_dist, method='single')   # Corretto da 'simple' a 'single'
Z_c = linkage(X_dist, method='complete')
Z_a = linkage(X_dist, method='average')

# 3. Visualizzazione dei Dendrogrammi con etichette leggibili
fig, axs = plt.subplots(1, 3, figsize=(20, 7))

# Single
dendrogram(Z_s, ax=axs[0], no_labels = True, leaf_rotation=90, leaf_font_size=8)
axs[0].set_title("Euclidean - Single Linkage (Legame Singolo)")

# Complete
dendrogram(Z_c, ax=axs[1], no_labels = True, leaf_rotation=90, leaf_font_size=8)
axs[1].set_title("Euclidean - Complete Linkage (Legame Massimo)")

# Average
dendrogram(Z_a, ax=axs[2], no_labels = True, leaf_rotation=90, leaf_font_size=8)
axs[2].set_title("Euclidean - Average Linkage (Legame Medio)")

plt.suptitle("Confronto dei Dendrogrammi - Algoritmi Spiegati a Lezione", y=1.05, fontsize=14, weight='bold')
plt.tight_layout()
plt.show()

_save_all_figures('cell_74_Clusters, No cut')

# %% [markdown] cell 75
# Cophenetic Distances

# %% cell 76
c_single, _ = cophenet(Z_s, X_dist)
c_complete, _ = cophenet(Z_c, X_dist)
c_average, _ = cophenet(Z_a, X_dist)

print(f"Cophenetic Coeff.- Single Linkage:   {c_single:.4f}")
print(f"Cophenetic Coeff.- Complete Linkage: {c_complete:.4f}")
print(f"Cophenetic Coeff.- Average Linkage:  {c_average:.4f}")

_save_all_figures('cell_76_Cophenetic Distances')

# %% [markdown] cell 77
# We choose Average Linkage

# %% [markdown] cell 78
# When to cut? WSS and BSS minimizing

# %% cell 79
#Function
 
def compute_internal_measures(x, merges, k_values):
    wss_values = {}
    bss_values = {}

    overall_mean = np.mean(x, axis=0)  # Compute global mean

    for k in k_values:
        clustering = fcluster(merges, k, criterion='maxclust')
        # computes centroids for all clusters
        centroids = [np.mean(x[clustering==c],axis=0) for c in range(1,k+1)]
        cluster_sizes = [len(x[clustering==c]) for c in range(1,k+1)]
        # computes the euclidean distance between each point and each centroid
        D = cdist(x, centroids, 'euclidean')
        # find nearest centroid for each point
        cIdx = np.argmin(D,axis=1)
        # store the distances to the nearest centroid
        d = np.min(D,axis=1)

        # WSS
        wss = sum(d**2)

        # BSS
        bss = np.sum([size * np.sum((centroid - overall_mean) ** 2) for size, centroid in zip(cluster_sizes, centroids)])

        wss_values[k] = wss
        bss_values[k] = bss
    return wss_values,bss_values

_save_all_figures('cell_79_When to cut? WSS and BSS minimizing')

# %% [markdown] cell 80
#

# %% cell 81
k_values = range(1,20)
wss_dict, bss_dict = compute_internal_measures(X_scaled, Z_a, k_values)
wss_values = [wss_dict[x] for x in range(1,20)]
bss_values = [bss_dict[x] for x in range(1,20)]
fig = plt.figure(figsize=(8,6))
font = {'family' : 'sans', 'size'   : 16}
plt.rc('font', **font)
plt.plot(k_values, wss_values, 'bo-', color='red', label='WSS')
plt.plot(k_values, bss_values, 'bo-', color='blue', label='BSS')
plt.grid(True)
plt.xlabel('Number of clusters')
plt.ylabel('BSS & WSS')
plt.xticks(k_values)
plt.legend()
plt.title('Hierarchical Clustering');

_save_all_figures('cell_81_cell_80')

# %% cell 82
clustering = fcluster(Z_a, 5, criterion='maxclust')
print(pd.Series(clustering).value_counts())

_save_all_figures('cell_82_cell_80')

# %% cell 83
clustering = fcluster(Z_a, 3, criterion='maxclust')
print(pd.Series(clustering).value_counts())

_save_all_figures('cell_83_cell_80')

# %% cell 84
# Assegniamo l'array 'clustering' (generato con K=5 e Complete Linkage) come colonna del DataFrame
# Assicurati di aver generato 'clustering' usando Z_c (Complete Linkage) e k=5
df_cluster['cluster_completato'] = clustering

# Stampiamo le cause contenute in ciascun cluster
print("--- COMPOSIZIONE REALE DEI CLUSTER (Complete Linkage, K=5) ---\n")

for numero_cluster in sorted(df_cluster['cluster_completato'].unique()):
    # Estraiamo le cause appartenenti a quel blocco
    cause_nel_cluster = df_cluster[df_cluster['cluster_completato'] == numero_cluster].index.tolist()
    
    print(f"=========================================")
    print(f"CLUSTER {numero_cluster} ({len(cause_nel_cluster)} micro-cause)")
    print(f"=========================================")
    
    # Stampiamo tutte le cause del cluster (una per riga per leggerle bene)
    for c in cause_nel_cluster:
        print(f" • {c}")
    print("\n")

_save_all_figures('cell_84_cell_80')

# %% [markdown] cell 85
# Chaining Effect, let's try with Complete

# %% cell 86
k_values = range(1,20)
wss_dict, bss_dict = compute_internal_measures(X_scaled, Z_c, k_values)
wss_values = [wss_dict[x] for x in range(1,20)]
bss_values = [bss_dict[x] for x in range(1,20)]
fig = plt.figure(figsize=(8,6))
font = {'family' : 'sans', 'size'   : 16}
plt.rc('font', **font)
plt.plot(k_values, wss_values, 'bo-', color='red', label='WSS')
plt.plot(k_values, bss_values, 'bo-', color='blue', label='BSS')
plt.grid(True)
plt.xlabel('Number of clusters')
plt.ylabel('BSS & WSS')
plt.xticks(k_values)
plt.legend()
plt.title('Hierarchical Clustering');

_save_all_figures("cell_86_Chaining Effect, let's try with Complete")

# %% cell 87
clustering = fcluster(Z_c, 3, criterion='maxclust')
print(pd.Series(clustering).value_counts())

_save_all_figures("cell_87_Chaining Effect, let's try with Complete")

# %% cell 88
clustering = fcluster(Z_c, 5, criterion='maxclust')
print(pd.Series(clustering).value_counts())

_save_all_figures("cell_88_Chaining Effect, let's try with Complete")

# %% cell 89
# Assegniamo l'array 'clustering' (generato con K=5 e Complete Linkage) come colonna del DataFrame
# Assicurati di aver generato 'clustering' usando Z_c (Complete Linkage) e k=5
df_cluster['cluster_completato'] = clustering

# Stampiamo le cause contenute in ciascun cluster
print("--- COMPOSIZIONE REALE DEI CLUSTER (Complete Linkage, K=5) ---\n")

for numero_cluster in sorted(df_cluster['cluster_completato'].unique()):
    # Estraiamo le cause appartenenti a quel blocco
    cause_nel_cluster = df_cluster[df_cluster['cluster_completato'] == numero_cluster].index.tolist()
    
    print(f"=========================================")
    print(f"CLUSTER {numero_cluster} ({len(cause_nel_cluster)} micro-cause)")
    print(f"=========================================")
    
    # Stampiamo tutte le cause del cluster (una per riga per leggerle bene)
    for c in cause_nel_cluster:
        print(f" • {c}")
    print("\n")

_save_all_figures("cell_89_Chaining Effect, let's try with Complete")

# %% cell 90
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Definiamo qual è la colonna dove hai salvato i cluster
colonna_cluster = 'cluster_completato' 

# 2. Selezioniamo solo le 5 feature numeriche e la colonna del cluster
features_numeriche = ['mortalita_rate', 'feriti_rate', 'quota_morti_conducenti', 'quota_morti_vulnerabili', 'morti_medi_annui']
df_boxplot = df_cluster[features_numeriche + [colonna_cluster]].copy()

# 3. Portiamo 'causa' da indice a colonna e applichiamo il melt
df_melt = df_boxplot.reset_index().melt(
    id_vars=['causa', colonna_cluster], 
    value_vars=features_numeriche,
    var_name='Feature', 
    value_name='Valore'
)

# 4. Creiamo il FacetGrid dinamico
g = sns.FacetGrid(
    df_melt, 
    col="Feature", 
    sharey=False, 
    hue=colonna_cluster, 
    palette="Set1", 
    height=4, 
    aspect=1.2,
    col_wrap=3
)

# Mappiamo il boxplot rimuovendo il parametro alpha problematico
ordine_cluster = sorted(df_cluster[colonna_cluster].unique())
g.map(sns.boxplot, colonna_cluster, "Valore", order=ordine_cluster)

# Pulizia estetica dei grafici
g.add_legend(title="Cluster")
g.set_titles("{col_name}", weight='bold')
g.set_axis_labels("Codice Cluster", "Valore")

# Spostiamo il titolo globale verso l'alto
plt.suptitle("Profilazione Geometrica dei Cluster - Analisi Boxplot delle Feature", y=1.02, fontsize=14, weight='bold')

plt.show()

_save_all_figures("cell_90_Chaining Effect, let's try with Complete")

# %% [markdown] cell 91
# # 9. Regressione lineare
#
# La regressione lineare e inclusa per coerenza con il progetto, ma sui conteggi non e il modello principale. La usiamo su un indicatore continuo: morti per 1.000 incidenti.

# %% cell 92
import statsmodels.formula.api as smf

model_df = cause_core.copy()
model_df = model_df[model_df['incidenti'] > 0].copy()
model_df['log_incidenti'] = np.log(model_df['incidenti'])
model_df['post_covid'] = (model_df['anno'] >= 2020).astype(int)

ols = smf.ols('mortalita_per_1000_incidenti ~ log_incidenti + quota_morti_pedoni_pct + quota_morti_trasportati_pct + C(macro_categoria) + anno', data=model_df).fit(cov_type='HC3')
print(ols.summary())

_save_all_figures('cell_92_9. Regressione lineare')

# %% [markdown] cell 93
# ## 10. Modelli di conteggio: Poisson e Negative Binomial
#
# Per i decessi ha piu senso modellare un conteggio. L'offset `log(incidenti)` trasforma il modello in una stima del tasso di mortalita a parita di numero di incidenti.

# %% cell 94
import statsmodels.api as sm

poisson = smf.glm('morti_totale ~ quota_morti_pedoni_pct + quota_morti_trasportati_pct + C(macro_categoria) + C(anno)',
                  data=model_df,
                  family=sm.families.Poisson(),
                  offset=np.log(model_df['incidenti'])).fit()
print(poisson.summary())
print('Overdispersion ratio:', poisson.pearson_chi2 / poisson.df_resid)

nb = smf.glm('morti_totale ~ quota_morti_pedoni_pct + quota_morti_trasportati_pct + C(macro_categoria) + C(anno)',
             data=model_df,
             family=sm.families.NegativeBinomial(),
             offset=np.log(model_df['incidenti'])).fit()
print(nb.summary())

_save_all_figures('cell_94_10. Modelli di conteggio: Poisson e Negative Binomial')

# %% [markdown] cell 95
# ## 11. Modelli predittivi e importanza delle variabili
#
# Questa parte serve per una lettura piu operativa: quali variabili aiutano maggiormente a prevedere il numero di morti?

# %% cell 96
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RidgeCV, LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

features = ['anno','incidenti','feriti_totale','morti_conducenti','morti_trasportati','morti_pedoni',
            'quota_morti_pedoni_pct','quota_morti_trasportati_pct','quota_incidenti_anno_pct','macro_categoria']
target = 'morti_totale'
ml_df = model_df[features + [target]].dropna().copy()

# Per evitare leakage forte, togli queste tre colonne se vuoi prevedere morti_totale senza usare componenti dei morti.
features_no_leakage = ['anno','incidenti','feriti_totale','quota_incidenti_anno_pct','macro_categoria']

X = ml_df[features_no_leakage]
y = ml_df[target]
num_features = [c for c in features_no_leakage if c != 'macro_categoria']
cat_features = ['macro_categoria']
pre = ColumnTransformer([('num', StandardScaler(), num_features), ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.25, random_state=42)
models = {
    'Ridge': RidgeCV(alphas=np.logspace(-3,3,20)),
    'Lasso': LassoCV(cv=5, random_state=42, max_iter=20000),
    'RandomForest': RandomForestRegressor(n_estimators=500, random_state=42, min_samples_leaf=3)
}

results = []
fitted = {}
for name, estimator in models.items():
    pipe = Pipeline([('pre', pre), ('model', estimator)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    results.append({'modello': name, 'MAE_test': mean_absolute_error(y_test, pred), 'R2_test': r2_score(y_test, pred)})
    fitted[name] = pipe
display(pd.DataFrame(results).sort_values('MAE_test'))

rf = fitted['RandomForest'].named_steps['model']
feature_names = fitted['RandomForest'].named_steps['pre'].get_feature_names_out()
importance = pd.DataFrame({'feature': feature_names, 'importance': rf.feature_importances_}).sort_values('importance', ascending=False)
display(importance.head(20))

_save_all_figures('cell_96_11. Modelli predittivi e importanza delle variabili')

# %% [markdown] cell 97
# ## 12. Sintesi per proposte di miglioramento
#
# Una proposta credibile dovrebbe distinguere tre priorita:
#
# 1. **Cause ad alto volume**: generano il maggior numero di incidenti e quindi hanno grande impatto sociale anche se il tasso di mortalita non e massimo.
# 2. **Cause ad alta letalita**: meno frequenti, ma con molti morti ogni 1.000 incidenti.
# 3. **Cause con vulnerabilita pedonale**: prioritarie per interventi su attraversamenti, velocita urbana, visibilita e separazione dei flussi.
#
# Nel report finale conviene presentare una matrice volume-severita: asse x = incidenti, asse y = mortalita per 1.000 incidenti, colore = quota morti pedoni, dimensione = morti totali.

# %% cell 98
if 'morti' not in ranking.columns:
    ranking['morti'] = ranking[['morti_conducenti', 'morti_trasportati', 'morti_pedoni']].sum(axis=1)
if 'mortalita_pool' not in ranking.columns:
    ranking['mortalita_pool'] = ranking['morti'] / ranking['incidenti'].replace(0, np.nan) * 1000
summary = ranking.merge(victim_profile[['causa','quota_pedoni_pct']], on='causa', how='left')
summary['priorita'] = np.select(
    [summary['incidenti'].ge(summary['incidenti'].quantile(.75)) & summary['mortalita_pool'].ge(summary['mortalita_pool'].median()),
     summary['mortalita_pool'].ge(summary['mortalita_pool'].quantile(.75)),
     summary['quota_pedoni_pct'].ge(50)],
    ['alto volume e severita', 'alta letalita', 'forte impatto pedoni'],
    default='monitoraggio')
display(summary.sort_values(['priorita','morti'], ascending=[True,False]).head(30))

plt.figure(figsize=(10,7))
sizes = 40 + 500 * summary['morti'] / summary['morti'].max()
sc = plt.scatter(summary['incidenti'], summary['mortalita_pool'], s=sizes, c=summary['quota_pedoni_pct'], cmap='viridis', alpha=.7)
plt.xscale('log')
plt.xlabel('Incidenti 2007-2024, scala log')
plt.ylabel('Morti per 1.000 incidenti')
plt.title('Matrice volume-severita delle cause')
plt.colorbar(sc, label='Quota morti pedoni (%)')
plt.show()

_save_all_figures('cell_98_12. Sintesi per proposte di miglioramento')
