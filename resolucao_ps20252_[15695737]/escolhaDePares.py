import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from volatility_check import volatility_check
def escolhePares():
    df = pd.read_csv("precos_b3_202010-2024_adjclose.csv", nrows = 1458) #coleta de dados irá até o dia 31/12/2013

    prop = df.notna().mean() #calcula a proporção de dados ausentes por coluna
    filtred_columns = prop[prop >= 1].index #pega as colunas que tem mais dados presentes de todos os dias
    df = df[filtred_columns] #atualiza o dataframe

    log_prices = np.log(df.select_dtypes(include=[np.number]))

    correlation_matrix = log_prices.corr()
    #aqui cria uma matriz de correlação onde o valor da célula [A][B] indica a correlação entre os ativos A e B
    #correlation_matrix.to_csv('correlation_matrix.csv', sep=';', index=True, header=True)

    empresas = []
    for i in range(len(correlation_matrix.index)):
        empresas.append(correlation_matrix.index[i])

    pairs = []
    for i in range(len(correlation_matrix.index)): #loop que acessa o triângulo inferior da matriz
        for j in range(len(correlation_matrix.columns)):
            if i > j:
                linha = correlation_matrix.index[i]
                coluna = correlation_matrix.columns[j]
                valor = correlation_matrix.loc[linha, coluna]
                if valor>=0.8: pairs.append([linha, coluna]) #se a correlação for maior que 0,8 adiciona o par na lista dos pares

    filtred_pairs = []
    sectors = pd.read_csv('sectors.csv', sep=';', index_col=0) #tabela de setores gerada por sectors.py

    for p in pairs: #filtra por setores
        if p[0] in sectors.index and p[1] in sectors.index:
            if sectors.loc[p[0]].values[0] == sectors.loc[p[1]].values[0]:
                filtred_pairs.append(p)
    pairs = filtred_pairs #atualiza os pares depois do filtro de setor



    filtred_pairs = []
    for p in pairs: #filtro de cointegração (rejeição da hpótese nula pelo teste adfuller)
        df_pair = pd.concat([df[p[0]], df[p[1]]], axis=1).dropna() #concatena os dois tickers para ignorar as linhas com dados ausentes
        #precisa tirar as linhas NaN porque o modelo OLS não funciona se tiver dado ausente
        ticker1 = df_pair[p[0]] #recupera a informação de cada ticker passando para as váriaveis
        ticker2 = df_pair[p[1]] #no final esse bloco serve para remover dados ausentes

        X = sm.add_constant(ticker2)
        model = sm.OLS(ticker1, X).fit() #usa o metodo dos minimos quadrados ordinarios
        beta = model.params.iloc[1] #beta verifica se as ações tem comportamento de "X" (se inverterem)
        residuos = model.resid
        #esse trecho cria uma regressão linear simples entre os tickers e coleta os resíduos
        #os resíduos são a diferença entre o valor observado (ticker1[i]) e o valor previsto pelo modelo (ŷ[i])
        adf_result = adfuller(residuos)
        p_value = adf_result[1] #o adfuller retorna uma tupla, e o valor que eu quero verificar  está na segunda posição
        #p_value <= 0.1 (p-valor do teste da raiz unitária) rejeita a hipótese nula do ADF e portanto garante ser uma série estacionária
        spread_abs_medio = (abs(residuos)/ticker1).mean() #essa variável será responsável por filtrar pela média dos spreads
        if p_value <= 0.1 and spread_abs_medio < 0.1 and beta>0:
            filtred_pairs.append(p)
    pairs = filtred_pairs
    


    filtred_pairs = []
    for p in pairs: #esse filtro de proporção de medianas, ou seja, ações fora de escala uma com a outra de forma a limpar as "penny stocks"
        pa, pb = df[p[0]].median(), df[p[1]].median() #pa e pb são as medianas dos preços
        if pa > 0 and pb > 0 and pd.isna(pa) == False and pd.isna(pb) == False:
            if max(pa,pb)/min(pa,pb) <= 4: #remove ações que tem mediana 4x maiores ou menores que seu par
                filtred_pairs.append(p)
    pairs = filtred_pairs

    filtred_pairs = []
    for p in pairs: # mede volatilidade com base na volatilidade do IBOV, para assim o modelo se adaptar a momentos diferentes do mercado
        if volatility_check(p[0]) == True and volatility_check(p[1]) == True:
            filtred_pairs.append(p)
    pairs = filtred_pairs

    filtred_pairs = []
    for p in pairs: #garante uma amplitude mínima dos preços para evitar ações com pouca variação
        range1 = (df[p[0]].max() - df[p[0]].min())/df[p[0]].min()
        range2 = (df[p[1]].max() - df[p[1]].min())/df[p[1]].min()

        if range1 >= 0.2 and range2 >= 0.2:
            filtred_pairs.append(p)
    pairs = filtred_pairs


    for p in pairs: #ordena os pares para deixar o com maior mediana na segunda posição (usarei direto pair2 como variável dependente na regressão para facilitar compreensão)
        if np.median(df[p[0]]) > np.median(df[p[1]]):
            p[0], p[1] = p[1], p[0]

    return pairs
    
