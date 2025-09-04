import pandas as pd
import yfinance as yf

df = pd.read_csv('precos_b3_202010-2024_adjclose.csv', nrows=1)

sectors = {}
i=0

for ticker in df: #a função primeiro verifica se ja tem aquele setor no dicionario, se não tiver faz a requisição e adiciona (otimiza o código)
        #depois verifica se os setores de cada ticker são iguais conferindo no dicionário
        i+=1
        print(i)
        if ticker not in sectors:
            try:
                sectors[ticker] = yf.Ticker(ticker).info.get("sector")
            except:
                sectors[ticker] = None

pd.Series(sectors, name='Setor').to_csv('sectors.csv', sep=';', header=True)