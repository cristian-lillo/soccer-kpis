import matplotlib.pyplot as plt
import pandas as pd

from config import paths

# ==================================
# 1. PAPERS DATA
# ==================================

# Create the DataFrame
papers_df = pd.read_json(paths.PAPERS_DATA_DIR / "papers_data.json", orient="index")
papers_df.columns = ["year", "data_type", "competitions", "seasons", "variables", "model_type"]

# ==========================================
# 2. ACADEMIC STYLE CONFIGURATION
# ==========================================
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 12,
        "axes.titlesize": 14,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": True,
    }
)

colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# ==========================================
# 3. CHART GENERATION
# ==========================================

plots_folder = paths.FIGURES_OUTPUT_DIR / "systematic_review"

# Chart 1: Temporal Evolution (Bar Chart)
plt.figure(figsize=(7, 4))
year_counts = papers_df["year"].value_counts().sort_index()
plt.bar(year_counts.index, year_counts.explode(), color=colors[0], width=0.6, zorder=3)
plt.grid(axis="y", linestyle="--", alpha=0.7, zorder=0)
plt.xticks(year_counts.index)
plt.yticks(range(0, int(year_counts.max()) + 2))
plt.xlabel("Año de Publicación")
plt.ylabel("Cantidad de Artículos")
plt.savefig(f"{plots_folder}/papers_anno_publicacion.pdf", bbox_inches="tight")
plt.close()

# Chart 2: Data Types (Donut Chart)
plt.figure(figsize=(6, 6))
exploded_data_type = papers_df["data_type"].explode()
data_type_counts = exploded_data_type.value_counts()
total_data_types = data_type_counts.sum() / 100.0
plt.pie(
    data_type_counts.values,
    labels=data_type_counts.index,
    autopct=lambda x: "%d" % round(x * total_data_types),
    pctdistance=0.8,
    startangle=140,
    colors=colors,
    wedgeprops=dict(width=0.4, edgecolor="w"),
)
plt.savefig(f"{plots_folder}/papers_tipo_de_datos.pdf", bbox_inches="tight")
plt.close()

# Chart 3: Analyzed Competitions (Horizontal Bar Chart)
plt.figure(figsize=(7, 4))
df_exploded = papers_df.explode("competitions")
competition_counts = df_exploded["competitions"].value_counts().sort_values(ascending=True)

plt.barh(competition_counts.index, competition_counts.values, color=colors[2], zorder=3)
plt.grid(axis="x", linestyle="--", alpha=0.7, zorder=0)
plt.xticks(range(0, int(competition_counts.max()) + 2))
plt.xlabel("Frecuencia de Uso en Modelos")
plt.savefig(f"{plots_folder}/papers_competiciones.pdf", bbox_inches="tight")
plt.close()

# Chart 4: Model Types (Bar Chart)
plt.figure(figsize=(7, 4))
exploded_model_type = papers_df["model_type"].explode()
model_type_counts = exploded_model_type.value_counts()
plt.bar(model_type_counts.index, model_type_counts.values, color=colors[1], width=0.5, zorder=3)
plt.grid(axis="y", linestyle="--", alpha=0.7, zorder=0)
plt.yticks(range(0, int(model_type_counts.max()) + 2))
plt.ylabel("Cantidad de Artículos")
plt.savefig(f"{plots_folder}/papers_tipo_de_modelos.pdf", bbox_inches="tight")
plt.close()

# Chart 5: Variables and Actions Used (Horizontal Bar Chart)
plt.figure(figsize=(8, 6))  # Slightly taller to accommodate all variables
df_exploded_vars = papers_df.explode("variables")
variables_counts = df_exploded_vars["variables"].value_counts().sort_values(ascending=True)

# Using a different color from your palette (e.g., colors[4] which is purple, or colors[0])
plt.barh(variables_counts.index, variables_counts.values, color=colors[4], zorder=3)
plt.grid(axis="x", linestyle="--", alpha=0.7, zorder=0)
plt.xticks(range(0, int(variables_counts.max()) + 2))
plt.xlabel("Frecuencia de Uso en Modelos")
plt.savefig(f"{plots_folder}/papers_variables.pdf", bbox_inches="tight")
plt.close()

# Chart 6: Seasons and Years Analyzed (Horizontal Bar Chart)
plt.figure(figsize=(8, 6))  # Slightly taller to accommodate all seasons
df_exploded_seasons = papers_df.explode("seasons")

# Counting frequency and sorting by index (season name) to have a chronological order
# ascending=False makes the older years appear at the top of the chart
seasons_counts = df_exploded_seasons["seasons"].value_counts().sort_index(ascending=False)

plt.barh(seasons_counts.index, seasons_counts.values, color=colors[3], zorder=3)
plt.grid(axis="x", linestyle="--", alpha=0.7, zorder=0)
plt.xticks(range(0, int(seasons_counts.max()) + 2))
plt.xlabel("Cantidad de Artículos")
plt.savefig(f"{plots_folder}/papers_temporadas.pdf", bbox_inches="tight")
plt.close()

print("Process completed! The 6 charts have been saved.")
