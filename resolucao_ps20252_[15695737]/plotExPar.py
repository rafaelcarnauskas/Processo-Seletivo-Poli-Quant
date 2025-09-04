import matplotlib.pyplot as plt
import pandas as pd

#esse codigo foi inteiro gerado por engenharia de prompt

df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", nrows = 1458)

pares = [('GOAU3.SA', 'VALE3.SA')]
returns = df

color_map = plt.colormaps['tab10']  # 10 cores distintas

# Como é apenas um par, simplifica
fig, ax = plt.subplots(figsize=(12, 6))

for col1, col2 in pares:
    if col1 in returns.columns and col2 in returns.columns:
        ax.plot(returns.index, returns[col1], color=color_map(0), linestyle='-', label=col1)
        ax.plot(returns.index, returns[col2], color=color_map(1), linestyle='-', label=col2)
        ax.set_title(f'{col1} x {col2}')
        ax.legend()
        ax.set_ylabel('Preço')
        ax.grid(True)

plt.xlabel('Data')
plt.suptitle('Preços diários')
plt.tight_layout()
plt.show()
