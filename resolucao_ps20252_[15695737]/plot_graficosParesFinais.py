import matplotlib.pyplot as plt
import pandas as pd
import math
from escolhaDePares import escolhePares

df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", nrows=1458)

pares = escolhePares()
returns = df

n = len(pares)
cols = 3  # número de colunas de subplots
rows = math.ceil(n / cols)

fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 3*rows), sharex=True)
axes = axes.flat if n > 1 else [axes]

color_map = plt.colormaps['tab10']  # 10 cores distintas

for i, (col1, col2) in enumerate(pares):
    ax = axes[i]
    if col1 in returns.columns and col2 in returns.columns:
        ax.plot(returns.index, returns[col1], color=color_map(0), linestyle='-', label=col1)
        ax.plot(returns.index, returns[col2], color=color_map(1), linestyle='-', label=col2)
        ax.set_title(f'{col1} x {col2}')
        ax.legend()
        ax.set_ylabel('Preço')
        ax.grid(True)

for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])  # remove subplots não usados

plt.xlabel('Data')
plt.suptitle('Preços diários')
plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.show()
