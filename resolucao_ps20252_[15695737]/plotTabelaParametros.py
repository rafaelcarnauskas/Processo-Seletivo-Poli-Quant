import matplotlib.pyplot as plt

# Dados da tabela 2x4 (2 colunas, 4 linhas)
table_data = [
    ['Parâmetro', 'Valor'],
    ['MAX_EXPOSURE', '100%'],
    ['TRAILING_STOP', '2%'],
    ['STOP_LOSS', '-2%'],
    ['THRESHOLD', '0,5'],
    ['MAX_TRADING', '3']
]

fig, ax = plt.subplots(figsize=(8, 5))
ax.axis('off')

# Criar tabela
table = ax.table(cellText=table_data[1:],  # dados sem header
                colLabels=table_data[0],   # header
                cellLoc='center',
                loc='center',
                colColours=['lightblue', 'lightgreen'])

# Formatação
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.5, 2)  # largura, altura das células

# Formatação das células
for i in range(len(table_data)):
    for j in range(len(table_data[0])):
        cell = table[(i, j)]
        if i == 0:  # header
            cell.set_text_props(weight='bold')
            cell.set_facecolor('navy')
            cell.set_text_props(color='white')
        else:
            # Alternar cores das linhas
            if i % 2 == 0:
                cell.set_facecolor('#f8f9fa')
            else:
                cell.set_facecolor('#e9ecef')

plt.title('Parâmetros do Backtest', fontsize=16, weight='bold', pad=20)
plt.savefig('tabela_parametros.png', dpi=300, bbox_inches='tight')
plt.show()