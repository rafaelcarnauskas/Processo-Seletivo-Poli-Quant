import statsmodels.api as sm
from escolhaDePares import escolhePares
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def rolling_window(name1, name2, df, end, window): #função de cálculo do beta da regressão em rolling window
    ticker1 = df[name1].iloc[end - window:end]
    ticker2 = df[name2].iloc[end - window:end]

    # regressão OLS: ticker2 ~ beta * ticker1, alfa==0 por serem cointegrados (intercepto na origem)
    model = sm.OLS(ticker2, ticker1, hasconst=False).fit()
    beta_window = model.params.iloc[0]

    #o valor do beta não altera significativamente todo dia pois apenas troca o primeiro pelo próximo, então o beta demora para variar significativamente
    return {"betas": beta_window}

def generateTradeSignal():
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv") #coleta de dados em 1458 dias e o resto em treino
    
    pairs = escolhePares() #retorna a lista dos pares escolhidos

    tickers = []
    for pair in pairs:#cria uma lista de dicts para cada par, facilitando a organização das informações
        pair_dict = {'pairs': pair, 'betas': [], 'spreads': [], 'zscores': []}
        tickers.append(pair_dict)

    for pair_dict in tickers:
        name1, name2 = pair_dict['pairs']
        current_beta = None
        #loop principal
        for i in range(1458, len(df)): #começa em 1458 pois antes disso é coleta de dados para escolha de pares
                
            window_data = rolling_window(name1, name2, df, i-1, 31) #uso o dia anterior como ultimo ponto para coleta de dados em rolling window
            current_beta = window_data['betas'] #captura o beta da janela
            pair_dict['betas'].append(current_beta)
            
            # calcula spread e zscore diários usando o beta atual
            ticker1 = df[name1].iloc[i]  # pegando o valor do dia atual
            ticker2 = df[name2].iloc[i]
            
            # calcula spread com o beta atual (relembrando que spread é a diferença entre valor real e valor estimado)
            spread = ticker2 - (current_beta * ticker1)
            pair_dict['spreads'].append(spread)
            
            # calcula zscore com média e desvio móveis
            historical_spreads = pd.Series(pair_dict['spreads'])
            if len(historical_spreads) >= 31:  # só calcula zscore quando tiver dados suficientes
                spread_mean = historical_spreads.rolling(31).mean().iloc[-1]
                spread_std = historical_spreads.rolling(31).std().iloc[-1]
                zscore = (spread - spread_mean) / spread_std
            else:
                zscore = 0  #valores de zscore ficam zerados antes da primeira janela
                
            pair_dict['zscores'].append(zscore)

    return tickers

def trade(tickers, df):
    for pair_dict in tickers:

        pair1, pair2 = pair_dict['pairs']
        capital_inicial = 1000000 #1 milhão de reais
        
        cash = capital_inicial
        position = [0,0] #lista que vai guardar a quantidade de cada ativo, onde p ativo1 é o mais barato e o ativo2 é o mais caro, pelo menos no começo do trade

        STOP_LOSS = -0.02 # garante que a perda acumulada em relação ao capital inicial não ultrapasse 2%
        TRAILING_STOP = 0.02 # garante que a perda acumulada em relação a um pico de equity não ultrapasse 2%
        MAX_EXPOSURE = 1 # controla a quantidade máxima de exposição do caixa em uma trade

        PnL_history = [] #guarda o PnL diario, útil para analisar a curva de Profit and Loss (PnL)
        cash_evolution = [] #guarda a curva de evolução do caixa
        MAX_TRADING = 3 #quantidade máxima de alocações a serem feitas antes de fechar a posição
        NUM_TRADING  = 0 #conta a quantidade de alocações antes de fechar a posição
        retorno = 0 #equity = valor em caixa + valor em ações (tanto que podem ser vendidas quanto as que devem ser compradas)

        for i in range(1458, len(df)):
            price1 = df[pair1].iloc[i]
            price2 = df[pair2].iloc[i]
            beta   = pair_dict['betas'][i-1458]
            zscore = pair_dict['zscores'][i-1458] #pega o valor atual
            cash_free = MAX_EXPOSURE*cash #caixa livre para uso em alocações
            retorno = cash + position[0]*price1 + position[1]*price2 #equity

            if position is None or position == [0,0]:  # sem trade aberto

                if zscore > 2: #spread maior que o normal
                    # short em ticker2 e long em ticker1
                    position, delta_cash = alocation(price1, price2, beta, cash_free, None, "SET_LONG1_SHORT2")
                    cash-=delta_cash #atualiza o caixa total
                    NUM_TRADING+=1
                elif zscore < -2: #spread menor que o normal
                    # short em ticker1 e long em ticker2
                    position, delta_cash = alocation(price1, price2, beta, cash_free, None, "SET_LONG2_SHORT1")
                    cash-=delta_cash
                    NUM_TRADING+=1

            else:  # já tem trade aberto
                if abs(zscore) < 0.5: #spread na faixa normal
                    position, delta_cash = alocation(price1, price2, beta, None, position, "CLOSE_OPERATION")
                    cash += delta_cash
                    NUM_TRADING = 0

                elif retorno < (1+STOP_LOSS)*capital_inicial: #perda acumulada em relação ao capital inicial
                    position, delta_cash = alocation(price1, price2, beta, None, position, "STOP_LOSS")
                    cash += delta_cash
                    NUM_TRADING = 0

                else: # alocação escalonada: NUM_TRADING controla a quantidade de trades e o cash_free é passado em proporções menores para protegr a carteira
                    #segue a mesma lógica das condições das linhas 89 e 94
                    if NUM_TRADING < MAX_TRADING:
                        if 2.5 < zscore <= 3.0:
                            new_position, delta_cash = alocation(price1, price2, beta, cash_free*0.2, position, "SET_LONG1_SHORT2") #usa apenas 20% do cash disponível
                            cash-=delta_cash
                            position = [position[0] + new_position[0], position[1] + new_position[1]]
                            NUM_TRADING+=1
                        elif -3.0 <= zscore < -2.5:
                            new_position, delta_cash = alocation(price1, price2, beta, cash_free*0.2, position, "SET_LONG2_SHORT1")
                            cash-=delta_cash
                            position = [position[0] + new_position[0], position[1] + new_position[1]]
                            NUM_TRADING+=1

                        if zscore > 3.0:
                            new_position, delta_cash = alocation(price1, price2, beta, cash_free*0.1, position, "SET_LONG1_SHORT2") #usa apenas 10% do cash disponível
                            cash-=delta_cash
                            position = [position[0] + new_position[0], position[1] + new_position[1]]
                            NUM_TRADING+=1
                        elif zscore < -3.0:
                            new_position, delta_cash = alocation(price1, price2, beta, cash_free*0.1, position, "SET_LONG2_SHORT1")
                            cash-=delta_cash
                            position = [position[0] + new_position[0], position[1] + new_position[1]]
                            NUM_TRADING+=1


            if position is None or position == [0,0]: #registra o pnl sem posição aberta
                PnL_today = cash
            else: #registra o pnl com posição aberta
                PnL_today = cash + price1*position[0] + price2*position[1]

            pos_clean = [float(x) for x in position] if position else None #deixa a notação mais legível

            PnL_history.append(PnL_today)
            cash_evolution.append(cash)

            equity = cash if position == [0,0] else cash + price1*position[0] + price2*position[1]

            if position == [0,0]:
                trail_peak = None  # reseta quando está flat
            else:
                trail_peak = equity if trail_peak is None else max(trail_peak, equity) #atualiza o pico de equity
                if equity <= trail_peak * (1 - TRAILING_STOP): #fecha a posição se o equity cair 2% em relação ao pico de equity
                    position, delta_cash = alocation(price1, price2, beta, None, position, "STOP_LOSS")
                    cash += delta_cash
                    trail_peak = None
                    NUM_TRADING = 0


        if position != [0,0] and position is not None: #fecha se tiver alocação remanescente
            position, delta_cash = alocation(price1, price2, beta, None, position, "CLOSE_OPERATION")
            cash += delta_cash
            cash_evolution.append(cash)  


        pair_dict['pnl_history'] = PnL_history
        pair_dict['cash_evolution'] = cash_evolution
        pair_dict['final_cash'] = PnL_history[-1]

    return tickers


def alocation(price1, price2, beta, cash_free, position, signal):
    

    if signal == "SET_LONG1_SHORT2":
        q2 = cash_free//(price2 + beta*price1)   # número de ações vendidas a descoberto (short selling)
        q1 = int(beta*q2) # número de ações compradas
        new_position = [q1, -q2]
        delta_cash = q1*price1 - q2*price2
        return new_position, delta_cash
    
    elif signal == "SET_LONG2_SHORT1":
        q2 = cash_free//(price2 + beta*price1)   # número de ações compradas
        q1 = int(beta*q2) # número de ações vendidas a descoberto
        new_position = [-q1, q2]
        delta_cash = -q1*price1 + q2*price2
        return new_position, delta_cash
    
    elif signal == "CLOSE_OPERATION": # zera toda a posição
        
        qA_total, qB_total = position
        delta_cash = -(qA_total * price1 + qB_total * price2)
        new_position = [0, 0]

        return new_position, delta_cash
    
    elif signal == "STOP_LOSS": # fecha 100% da posição

        qA_total = position[0]
        qB_total = position[1]
        
        qA_close = qA_total
        qB_close = qB_total

        delta_cash = price1 * qA_close + price2 * qB_close

        new_position = [0, 0]

        return new_position, delta_cash
    
if __name__ == "__main__":
    
    tickers = generateTradeSignal()
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv")

    tickers = trade(tickers, df)

    n = len(tickers)
    cols = 2
    rows = (n + cols - 1) // cols


    # gráfico evolução do portfólio-----------------------------
    plt.figure(figsize=(12, 5 * rows))
    for idx, pair_data in enumerate(tickers, 1):
        cash_evolution = pair_data['cash_evolution']
        dias = list(range(1458, 1458+len(cash_evolution)))
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"
        plt.subplot(rows, cols, idx)
        plt.plot(dias, cash_evolution, label='Evolução do caixa')
        plt.xlabel('Dia')
        plt.ylabel('Valor acumulado (Milhôes de R$)')
        plt.title(f'Par: {nome_par}')

        ax = plt.gca()
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x/1e6:.1f}'))

        # adiciona uma tag com valor final
        if len(cash_evolution) > 0:
            final_value = cash_evolution[-1]
            final_day = dias[-1]
            plt.annotate(f'R$ {final_value/1e6:.2f}M', 
                        xy=(final_day, final_value), 
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=9,
                        bbox=dict(boxstyle='round,pad=0.3', alpha=0.7),
                        ha='left')

        plt.legend()
        plt.grid(True)

    plt.tight_layout()
    plt.savefig("grafico_evolucaoParesFinais.png")
    plt.suptitle("Evolução do portólio")
    plt.show()

    # gráfico evolução de caixa de todos os pares-----------------------------
    plt.figure(figsize=(14, 8))
    
    for pair_data in tickers:
        cash_evolution = pair_data['cash_evolution']
        dias = list(range(1458, 1458+len(cash_evolution)))
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"
        plt.plot(dias, cash_evolution, label=nome_par, linewidth=2)
    
    plt.xlabel('Dia', fontsize=12)
    plt.ylabel('Valor acumulado (Milhões de R$)', fontsize=12)
    plt.title('Evolução dos Pares', fontsize=14, pad=15)
    
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x/1e6:.1f}'))
    plt.ylim(bottom=0)
    current_ticks = ax.get_yticks()
    new_ticks = sorted(list(current_ticks) + [1e6])
    ax.set_yticks(new_ticks)
    
    plt.axhline(y=1e6, color='black', linestyle='--', alpha=0.7, linewidth=2)
    
    plt.legend(loc='upper left', fontsize=12, framealpha=0.95, fancybox=True, shadow=True, borderpad=1)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("grafico_dos_pares.png", dpi=350, bbox_inches='tight')
    plt.show()

    for pair_data in tickers:
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"

    # gráfico análise zscore do par VALE3 - GOAU3-----------------------------
    for pair_dict in tickers:
        if 'VALE3.SA' in pair_dict['pairs'] and 'GOAU3.SA' in pair_dict['pairs']:
            dias = list(range(1458, 1458 + len(pair_dict['betas'])))
            
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

            fig.suptitle('Análise do par VALE3 - GOAU3', fontsize=14, y=0.99)
            
            ax1.plot(dias, pair_dict['betas'], 'navy', linewidth=1.5)
            ax1.set_title('Beta - VALE3.SA x GOAU3.SA', pad=10)
            ax1.grid(True, alpha=0.3)
            ax1.set_xlabel('Dia')
            ax1.set_ylabel('Beta')
            
            ax2.plot(dias, pair_dict['spreads'], 'coral', linewidth=1.5)
            ax2.set_title('Spread - VALE3.SA x GOAU3.SA', pad=10)
            ax2.grid(True, alpha=0.3)
            ax2.set_xlabel('Dia')
            ax2.set_ylabel('Spread')
            
            ax3.plot(dias, pair_dict['zscores'], 'teal', linewidth=1.5)
            ax3.set_title('Z-Score - VALE3.SA x GOAU3.SA', pad=10)
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=2, color='crimson', linestyle='--', alpha=0.7)
            ax3.axhline(y=-2, color='crimson', linestyle='--', alpha=0.7)
            ax3.set_xlabel('Dia')
            ax3.set_ylabel('Zscore')
            
            
            plt.subplots_adjust(left=0.061, bottom=0.06, right=0.987, top=0.9, hspace=0.505)
            plt.tight_layout()
            plt.savefig('grafico_analise_zscore.png', dpi=300, bbox_inches='tight')
            plt.show()
            break

    # gráfico valores finais de cada par-----------------------------
    nomes_pares = []
    valores_finais = []
    retornos_percentuais = []
    valor_total = 0
    
    for pair_data in tickers:
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"
        cash_evolution = pair_data['cash_evolution']
        
        if len(cash_evolution) > 0:
            valor_inicial = 1000000
            valor_final = cash_evolution[-1]
            retorno_absoluto = valor_final - valor_inicial
            retorno_percentual = (retorno_absoluto / valor_inicial) * 100
            valor_total += valor_final
            
            nomes_pares.append(nome_par.replace('.SA', ''))
            valores_finais.append(valor_final / 1e6)
            retornos_percentuais.append(retorno_percentual)
    fig, ax1 = plt.subplots(figsize=(16, 8))
    
    # eixo esquerdo com Rentabilidade (%)
    cores_retornos = ['teal' if r > 0 else 'red' for r in retornos_percentuais]
    bars1 = ax1.bar([x - 0.2 for x in range(len(nomes_pares))], retornos_percentuais, 
                    width=0.4, color=cores_retornos, alpha=0.7, edgecolor='black', 
                    label='Rentabilidade (%)')
    
    ax1.set_xlabel('Pares de Ações', fontsize=12, color = 'black')
    ax1.set_ylabel('Rentabilidade (%)', fontsize=12, color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.7, linewidth=2)
    for i, (bar, retorno) in enumerate(zip(bars1, retornos_percentuais)):
        height = bar.get_height()
        y_pos = height + (10 if height >= 0 else -30)
        ax1.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{retorno:.2f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                fontsize=9, fontweight='bold', color='black')
    
    # eixo direito com Valor Acumulado (R$ Milhões)
    ax2 = ax1.twinx()
    cores_valores = ['orange' if v > 1.0 else 'darkred' for v in valores_finais]
    bars2 = ax2.bar([x + 0.2 for x in range(len(nomes_pares))], valores_finais,
                    width=0.4, color=cores_valores, alpha=0.7, edgecolor='black',
                    label='Valor Final (R$ M)')
    
    ax2.set_ylabel('Valor Acumulado Final (R$ Milhões)', fontsize=12, color='black')
    ax2.tick_params(axis='y', labelcolor='black')
    for i, (bar, valor) in enumerate(zip(bars2, valores_finais)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{valor:.2f}M', ha='center', va='bottom', 
                fontsize=9, fontweight='bold', color='black')
    
    ax1.set_xticks(range(len(nomes_pares)))
    ax1.set_xticklabels(nomes_pares, rotation=45, ha='right')
    
    retorno_total_porcentual = ((valor_total - len(tickers)*1000000)/(len(tickers)*1000000))*100
    plt.title(f'Desempenho dos Pares: Rentabilidade vs Valor Acumulado\n'
             f'Valor inicial: 8M de reais |  Valor Final: {valor_total/1e6:.2f}M de reais |  Rentabilidade final: {retorno_total_porcentual:.2f}%', 
             fontsize=14, pad=20)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('grafico_desempenho_pares.png', dpi=300, bbox_inches='tight')
    plt.show()
    
