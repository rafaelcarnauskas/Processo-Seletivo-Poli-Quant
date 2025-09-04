import statsmodels.api as sm
from escolhaDePares import escolhePares
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def rolling_window(name1, name2, df, end, window): #função de cálculo do beta da regressão em rolling window
    ticker1 = df[name1].iloc[end - window:end]
    ticker2 = df[name2].iloc[end - window:end]

    # regressão OLS: ticker2 ~ beta * ticker1, alfa==0 por serem cointegrados (intercepto na origem)
    model = sm.OLS(ticker2, ticker1, hasconst=False).fit()
    beta_window = model.params.iloc[0]

    #o valor do beta não altera significativamente todo dia pois apenas troca o primeiro pelo próximo, então o beta demora para variar significativamente
    return {"betas": beta_window}

def generateTradeSignal():
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", nrows = 2191) #coleta de dados em 1458 dias e o resto em treino
    
    pairs = escolhePares() #retorna a lista dos pares escolhidos

    tickers = []
    for pair in pairs:#cria uma lista de dicts para cada par, facilitando a organização das informações
        pair_dict = {'pairs': pair, 'betas': [], 'spreads': [], 'zscores': []}
        tickers.append(pair_dict)

    for pair_dict in tickers:
        name1, name2 = pair_dict['pairs']
        current_beta = None
        # Loop principal
        for i in range(1458, 2191):
                
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

        with open("saida_ofc.txt", "w") as f: 
            for i in range(1458, 2191):
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
                print(f"Dia {i}: cash={cash:.2f}, price1={price1:.2f}, price2={price2:.2f}, position={pos_clean}, PnL_today={PnL_today:.2f}, zscore={zscore}", file=f) #gera os valores diários em saida.txt

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
            print(pair_dict['final_cash'], file=f) #escreve o caixa final no saida.txt

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
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", nrows = 2191)

    tickers = trade(tickers, df)

    n = len(tickers)
    cols = 2
    rows = (n + cols - 1) // cols

    plt.figure(figsize=(12, 5 * rows))
    for idx, pair_data in enumerate(tickers, 1):
        cash_evolution = pair_data['cash_evolution']
        dias = list(range(1458, 1458+len(cash_evolution)))
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"
        plt.subplot(rows, cols, idx)
        plt.plot(dias, cash_evolution, label='Evolução do caixa')
        plt.xlabel('Dia')
        plt.ylabel('Cash (R$)')
        plt.title(f'Par: {nome_par}')
        plt.legend()
        plt.grid(True)
    plt.tight_layout()
    plt.savefig("evolucaoParesFinais.png")
    plt.show()
    plt.suptitle("Evolução do portólio")

    for pair_data in tickers:
        nome_par = f"{pair_data['pairs'][0]} x {pair_data['pairs'][1]}"
