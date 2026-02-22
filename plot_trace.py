import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from constants import FORWARD, EAT, BUMP

# --- Load data ---
df = pd.read_csv("logs/00_trace.csv")

# --- X axis ---
x = df["step"]

# --- Create figure and main axis ---
fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()
ax3 = ax1.twinx()

# --- Plot e_length on ax1 (0–10) ---
ax1.plot(x, df["e_length"], label="Enacted schema length", marker="", color="tab:blue")
# ax1.set_ylabel("Enacted schema length")
ax1.set_ylim(-5, 20)

# --- Shared zero reference ---
ax1.axhline(0, linewidth=0.8, color="black")
ax1.set_xlabel("Step")
ax1.legend(loc="upper left")

# --- Plot nb_schemas on ax2 (0–200) ---
max_nb_schema = df["nb_schemas"].max()
ax2.plot(x, df["nb_schemas"], label="Nb schemas", marker="", color="tab:orange")
# ax2.set_ylabel("nb_schemas")
ax2.set_ylim(-max_nb_schema / 4, max_nb_schema)

ax2.legend(loc="upper right")

# --- Valence as bar graph on ax3 ---
# Small bars centered at zero
valence_colors = ["green" if v > 0 else "red" for v in df["valence"]]
ax3.bar(
    x,
    df["valence"],
    bottom=0,
    width=0.8,
    color=valence_colors,
    alpha=0.6,
    label="valence"
)

# --- Add squares for specific conditions on ax3 ---
# Red square: MOVE FORWARD and BUMP
mask_red = (df["code"] == FORWARD) & (df["outcome"] == BUMP)
ax3.scatter(
    df.loc[mask_red, "step"],
    # df.loc[mask_red, "e_length"],
    np.full(mask_red.sum(), -20),
    color="red",
    marker="s",
    s=50,
    zorder=5,
    label="Bump"
)

# Green square: Move FORWARD and EAT
mask_green = (df["code"] == FORWARD) & (df["outcome"] == EAT)
ax3.scatter(
    df.loc[mask_green, "step"],
    np.full(mask_green.sum(), -20),
    # df.loc[mask_green, "e_length"],
    color="lightgreen",
    marker="s",
    s=50,
    zorder=5,
    label="Eat"
)

ax3.set_ylim(-30, 200)
# ax3.set_xticks([])
ax3.set_yticks([])
# ax3.axis('off')
# ax3.legend(loc="lower left")

# --- Improve layout ---
plt.tight_layout()

# --- Show figure ---
plt.savefig("logs/00_trace_plot.svg")
plt.savefig("logs/00_trace_plot.pdf")
plt.show()
