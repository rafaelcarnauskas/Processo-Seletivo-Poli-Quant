import pandas as pd
import numpy as np

def volatility_check(ticker, window=63, threshold=0.8): #verifica a volatilidade em rolling window com o indice IBOV em uma janela de 63 dias
    ibov = pd.read_csv("ibov_2010_2024.csv", index_col=0, parse_dates=True, skiprows=[1])
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", index_col=0, parse_dates=True)

    #retornos logarítmicos (volatilidade)
    ibov_ret = np.log(ibov["Close"] / ibov["Close"].shift(1))
    stock_ret = np.log(df[ticker] / df[ticker].shift(1))

    # volatilidade rolling (desvio padrão dos retornos)
    ibov_vol = ibov_ret.rolling(window).std()
    stock_vol = stock_ret.rolling(window).std()

    # verifica se a volatilidade do ativo está entre 0.5x e 3x a do ibov
    inside_limits = (stock_vol >= 0.5 * ibov_vol) & (stock_vol <= 3 * ibov_vol)

    # proporção de dias dentro dos limites
    proportion_inside = inside_limits.mean()

    return proportion_inside >= threshold #retorna true se em 80% do tempo a ação tem volatilidade dentro do intervalo

def fixed_volatility(): # verifica a volatilidade fixando um valor (melhor usar a volatilidade relativa com o IBOV para melhorar adaptação do modelo)
    filtred_pairs = []
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", index_col=0, parse_dates=True, skiprows=2)
    for p in pairs: #filtro de volatilidade mínima diária = 0.5%
        
        log_returns1 = np.log(df[p[0]]/df[p[0]].shift(1))
        vol1 = log_returns1.std() #a volatilidade é o desvio padrão anualizado dos retornos logarítmicos

        log_returns2 = np.log(df[p[1]]/df[p[1]].shift(1))
        vol2 = log_returns2.std()

        if vol1 > 0.005 and vol2 > 0.005:
            filtred_pairs.append(p)
    pairs = filtred_pairs