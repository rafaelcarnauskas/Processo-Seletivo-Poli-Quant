import pandas as pd
import matplotlib.pyplot as plt
from backtest import trade
from backtest import generateTradeSignal

#bloco de análise ibov--------------------------------

df = pd.read_csv("ibov_2010_2024.csv")
# converte Close para valores numéricos e não strings
df["Close"] = pd.to_numeric(df["Close"].astype(str).str.replace(',', '.'), errors='coerce')

df["retorno"] = df["Close"].pct_change() #calcula os retornos diários (variação percentual)
df["retorno_acumulado"] = (1 + df["retorno"].iloc[1458:]).cumprod() #realiza os cálculos a partir do dia 1458

retorno_anualizado = (1 + df["retorno"].mean())**252 - 1 #anualiza o retorno médio diário via composição (252 dias úteis/ano)
volatilidade_anualizada = df["retorno"].std() * (252**0.5) #desvio padrão dos retornos multiplicados pela raíz da quantidade de dias
#pode calcular com valor do retorno logaritmo, mas para pequenas variações, como é o caso aqui, não muda nada
rentabilidade_final = df["retorno_acumulado"].iloc[-1] - 1  # Subtraindo 1 para ter apenas o ganho
df["Drawdown"] = df["Close"] / df["Close"].cummax() - 1 #calcula, em porcentagem, a queda em relação ao pico de retorno do período
drawdown_max = df["Drawdown"].min()

taxa_livre_risco = 0.089 #assumindo que CDI ~0.089% ao ano
sharpe_ibov = (retorno_anualizado-taxa_livre_risco)/volatilidade_anualizada

volatilidade_sortino_ibov = df["retorno"][df["retorno"] < 0].std() * (252**0.5)
sortino_ibov = (retorno_anualizado - taxa_livre_risco)/volatilidade_sortino_ibov

#bloco de análise portfólio--------------------------------

tickers = generateTradeSignal()
df_precos = pd.read_csv("precos_b3_202010-2024_adjclose.csv")
tickers = trade(tickers, df_precos)

evolucao_portfolio = [] #vai guardar a evolução de equity do portfólio
for day in range(len(tickers[0]['cash_evolution'])):
    total_day = sum(pair['cash_evolution'][day] for pair in tickers)
    evolucao_portfolio.append(total_day)

df_portfolio = pd.DataFrame({"evolucao_portfolio": evolucao_portfolio})
retorno_portfolio = df_portfolio["evolucao_portfolio"].pct_change()
df_portfolio["retorno_acumulado_portfolio"] = (1 + retorno_portfolio).cumprod()

retorno_anualizado_portfolio = (1 + retorno_portfolio.mean())**252 - 1
volatilidade_anualizada_portfolio = retorno_portfolio.std() * (252**0.5)
rentabilidade_final_portfolio = df_portfolio["retorno_acumulado_portfolio"].iloc[-1] - 1  # Subtraindo 1 para ter apenas o ganho

df_portfolio["Drawdown"] = df_portfolio["evolucao_portfolio"] / df_portfolio["evolucao_portfolio"].cummax() - 1 #calcula, em porcentagem, a queda em relação ao pico de retorno do período
drawdown_max_portfolio = df_portfolio["Drawdown"].min()

sharpe_portfolio = (retorno_anualizado_portfolio - taxa_livre_risco)/volatilidade_anualizada_portfolio
volatilidade_sortino_portfolio = retorno_portfolio[retorno_portfolio < 0].std() * (252**0.5)
sortino_portfolio = (retorno_anualizado_portfolio - taxa_livre_risco) / volatilidade_sortino_portfolio

#grafico portfolio X ibov---------------------

plt.figure(figsize=(12, 6))

ibov_retorno_percent = (df["retorno_acumulado"] - 1) * 100 + 100
portfolio_retorno_percent = (df_portfolio["retorno_acumulado_portfolio"] - 1) * 100 + 100

plt.plot(df.index, ibov_retorno_percent, label='IBOV', color='red')
dias_portfolio = range(1458, 1458 + len(df_portfolio))
plt.plot(dias_portfolio, portfolio_retorno_percent, label='Portfólio', color='blue')
plt.title("Comparação: Retorno Acumulado IBOV vs Portfólio")
plt.xlabel("Dia")
plt.ylabel("Retorno Acumulado (%)")
plt.legend()
plt.grid(True)

# Adicionar linha de referência em 100% (investimento inicial)
plt.axhline(y=100, color='black', linestyle='--', alpha=0.7, linewidth=1)

plt.savefig('grafico_analise_desempenho.png', dpi=300, bbox_inches='tight')

#tabelas desempenhos------------------------

tabela_ibov = [
    ['Métrica', 'IBOV'],
    ['Retorno Anualizado', f'{retorno_anualizado:.2%}'],
    ['Volatilidade Anualizada', f'{volatilidade_anualizada:.2%}'],
    ['Rentabilidade Final', f'{rentabilidade_final:.2%}'],
    ['Drawdown Máximo', f'{drawdown_max:.2f}'],
    ['Sharpe Ratio', f'{sharpe_ibov:.2f}'],
    ['Sortino Ratio', f'{sortino_ibov:.2f}']
]

tabela_portfolio = [
    ['Métrica', 'Portfólio'],
    ['Retorno Anualizado', f'{retorno_anualizado_portfolio:.2%}'],
    ['Volatilidade Anualizada', f'{volatilidade_anualizada_portfolio:.2%}'],
    ['Rentabilidade Final', f'{rentabilidade_final_portfolio:.2%}'],
    ['Drawdown Máximo', f'{drawdown_max_portfolio:.2f}'],
    ['Sharpe Ratio', f'{sharpe_portfolio:.2f}'],
    ['Sortino Ratio', f'{sortino_portfolio:.2f}']
]

# Criar figura com dois subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Tabela IBOV
ax1.axis('off')
table1 = ax1.table(cellText=tabela_ibov[1:],
                   colLabels=tabela_ibov[0],
                   cellLoc='center',
                   loc='center')
table1.auto_set_font_size(False)
table1.set_fontsize(12)
table1.scale(1.2, 2)

# Formatação tabela IBOV
for i in range(len(tabela_ibov)):
    for j in range(len(tabela_ibov[0])):
        cell = table1[(i, j)]
        if i == 0:  # header
            cell.set_text_props(weight='bold')
            cell.set_facecolor('blue')
            cell.set_text_props(color='white')
        else:
            if i % 2 == 0:
                cell.set_facecolor('#f8f9fa')
            else:
                cell.set_facecolor('#e9ecef')

ax1.set_title('', fontsize=16, weight='bold', pad=20)

# Tabela Portfólio
ax2.axis('off')
table2 = ax2.table(cellText=tabela_portfolio[1:],
                   colLabels=tabela_portfolio[0],
                   cellLoc='center',
                   loc='center')
table2.auto_set_font_size(False)
table2.set_fontsize(12)
table2.scale(1.2, 2)

# Formatação tabela Portfólio
for i in range(len(tabela_portfolio)):
    for j in range(len(tabela_portfolio[0])):
        cell = table2[(i, j)]
        if i == 0:  # header
            cell.set_text_props(weight='bold')
            cell.set_facecolor('teal')
            cell.set_text_props(color='white')
        else:
            if i % 2 == 0:
                cell.set_facecolor('#f8f9fa')
            else:
                cell.set_facecolor('#e9ecef')

ax2.set_title('', fontsize=16, weight='bold', pad=20)

plt.suptitle('Comparação de Performance: IBOV vs Portfólio', 
             fontsize=18, weight='bold', y=0.75)
plt.tight_layout()
plt.savefig('tabela_desempenhos.png', dpi=300, bbox_inches='tight')
plt.show()

