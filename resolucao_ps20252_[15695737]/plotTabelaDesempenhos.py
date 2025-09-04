import matplotlib.pyplot as plt

# Dados da tabela 2x4 (2 colunas, 4 linhas)
table_data = [
    ['Rentabilidade Final', '568.49%'],
    ['Volatilidade Anualizada', '8.96%'],
    ['Drawdown Máximo', '-7%'],
    ['Sharpe Ratio', 'não sei ainda'],
    ['Sortino Ratio', 'não sei ainda'],
    ['Retorno anualizado', '21.81%']
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
            cell.set_facecolor('white')  # Fundo azul escuro
            cell.set_text_props(color='black')  # Texto branco
        else:
            # Alternar cores das linhas
            if i % 2 == 0:
                cell.set_facecolor('#f8f9fa')
            else:
                cell.set_facecolor('#e9ecef')

plt.title('Desempenho do Portfólio', fontsize=16, weight='bold', pad=20)
plt.savefig('tabela_desempenhoP.png', dpi=300, bbox_inches='tight')
plt.show()