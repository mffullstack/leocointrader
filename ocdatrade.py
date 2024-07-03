import streamlit as st
import ccxt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

# Lista de exchanges suportadas pelo ccxt
exchanges = ['binance', 'coinbasepro', 'kraken', 'bitstamp']

# Função para obter o preço de uma criptomoeda em uma exchange específica
def get_price(exchange_name, symbol):
    exchange = getattr(ccxt, exchange_name)()
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

# Função para encontrar o preço mais barato e mais caro entre as exchanges
def find_cheapest_and_most_expensive(symbol):
    cheapest_exchange = ''
    most_expensive_exchange = ''
    cheapest_price = float('inf')
    most_expensive_price = 0.0

    for exchange_name in exchanges:
        try:
            price = get_price(exchange_name, symbol)
            if price < cheapest_price:
                cheapest_price = price
                cheapest_exchange = exchange_name
            if price > most_expensive_price:
                most_expensive_price = price
                most_expensive_exchange = exchange_name
        except Exception as e:
            st.warning(f"Erro ao obter preço na exchange {exchange_name}: {str(e)}")

    return cheapest_exchange, cheapest_price, most_expensive_exchange, most_expensive_price

# Função para calcular as bandas de Bollinger
def calculate_bollinger_bands(exchange_name, symbol, cheapest=True):
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=20)  # Obtém os últimos 20 dias de dados OHLCV
    close_prices = np.array([ohlcv[i][4] for i in range(len(ohlcv))])  # Obtém apenas os preços de fechamento
    period = 20  # Período para a média móvel e desvio padrão
    sma = np.mean(close_prices)
    std_dev = np.std(close_prices)
    upper_band = sma + 2 * std_dev
    lower_band = sma - 2 * std_dev
    
    if cheapest:
        return close_prices, sma, upper_band, lower_band, exchange_name
    else:
        return close_prices, sma, upper_band, lower_band, exchange_name

# Função para calcular o MACD
def calculate_macd(exchange_name, symbol, cheapest=True):
    exchange = getattr(ccxt, exchange_name)()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=100)  # Obtém os últimos 100 dias de dados OHLCV
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    if cheapest:
        title = f'MACD de {symbol} na {exchange_name} (mais barata)'
    else:
        title = f'MACD de {symbol} na {exchange_name} (mais cara)'
    
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    return macd, signal, histogram, df['timestamp'], title

# Interface do usuário com Streamlit
def main():
    st.title('Verificador de Preço de Criptomoedas')

    symbol = st.text_input('Digite o símbolo da criptomoeda (por exemplo, BTC/USD):')

    if st.button('Verificar Preço'):
        if symbol:
            cheapest_exchange, cheapest_price, most_expensive_exchange, most_expensive_price = find_cheapest_and_most_expensive(symbol)
            st.write(f'**Preço mais barato:** {cheapest_price} USD na exchange {cheapest_exchange}')
            st.write(f'**Preço mais caro:** {most_expensive_price} USD na exchange {most_expensive_exchange}')

            # Gráfico de linha para mostrar onde o preço está mais barato e mais caro
            plt.figure(figsize=(12, 24))  # Ajuste a altura para acomodar quatro gráficos verticalmente
            
            # Gráfico para comparar preço mais barato e mais caro
            plt.subplot(4, 1, 1)
            prices = [cheapest_price, most_expensive_price]
            exchanges = [cheapest_exchange, most_expensive_exchange]
            plt.plot(exchanges, prices, marker='o', linestyle='-', color='purple')
            plt.title(f'Preço mais barato e mais caro de {symbol}')
            plt.xlabel('Exchange')
            plt.ylabel('Preço (USD)')
            plt.grid(True)
            plt.tight_layout()

            # Gráfico para a exchange mais barata - Bandas de Bollinger
            plt.subplot(4, 1, 2)
            close_prices_cheapest, sma_cheapest, upper_band_cheapest, lower_band_cheapest, exchange_cheapest = calculate_bollinger_bands(cheapest_exchange, symbol, cheapest=True)
            plt.plot(close_prices_cheapest, label='Preço de Fechamento', color='blue')
            plt.plot([sma_cheapest] * len(close_prices_cheapest), label='Média Móvel Simples', linestyle='--', color='orange')
            plt.plot([upper_band_cheapest] * len(close_prices_cheapest), label='Banda Superior', linestyle='-.', color='red')
            plt.plot([lower_band_cheapest] * len(close_prices_cheapest), label='Banda Inferior', linestyle='-.', color='green')
            plt.fill_between(np.arange(len(close_prices_cheapest)), upper_band_cheapest, lower_band_cheapest, color='gray', alpha=0.1)
            plt.title(f'Bandas de Bollinger de {symbol} na {exchange_cheapest} (mais barata)')
            plt.xlabel('Dias')
            plt.ylabel('Preço (USD)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            # Resumo da exchange mais barata
            st.markdown(f"**Resumo - {cheapest_exchange} (mais barata):**\n"
                        f"- **Média Móvel Simples (20 dias):** {sma_cheapest:.2f} USD\n"
                        f"- **Banda Superior:** {upper_band_cheapest:.2f} USD\n"
                        f"- **Banda Inferior:** {lower_band_cheapest:.2f} USD")
            
            # Gráfico para a exchange mais cara - Bandas de Bollinger
            plt.subplot(4, 1, 3)
            close_prices_most_expensive, sma_most_expensive, upper_band_most_expensive, lower_band_most_expensive, exchange_most_expensive = calculate_bollinger_bands(most_expensive_exchange, symbol, cheapest=False)
            plt.plot(close_prices_most_expensive, label='Preço de Fechamento', color='blue')
            plt.plot([sma_most_expensive] * len(close_prices_most_expensive), label='Média Móvel Simples', linestyle='--', color='orange')
            plt.plot([upper_band_most_expensive] * len(close_prices_most_expensive), label='Banda Superior', linestyle='-.', color='red')
            plt.plot([lower_band_most_expensive] * len(close_prices_most_expensive), label='Banda Inferior', linestyle='-.', color='green')
            plt.fill_between(np.arange(len(close_prices_most_expensive)), upper_band_most_expensive, lower_band_most_expensive, color='gray', alpha=0.1)
            plt.title(f'Bandas de Bollinger de {symbol} na {exchange_most_expensive} (mais cara)')
            plt.xlabel('Dias')
            plt.ylabel('Preço (USD)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            # Resumo da exchange mais cara
            st.markdown(f"**Resumo - {most_expensive_exchange} (mais cara):**\n"
                        f"- **Média Móvel Simples (20 dias):** {sma_most_expensive:.2f} USD\n"
                        f"- **Banda Superior:** {upper_band_most_expensive:.2f} USD\n"
                        f"- **Banda Inferior:** {lower_band_most_expensive:.2f} USD")

            # Gráfico para a exchange mais cara - MACD
            plt.subplot(4, 1, 4)
            macd_most_expensive, signal_most_expensive, histogram_most_expensive, dates, title_most_expensive = calculate_macd(most_expensive_exchange, symbol, cheapest=False)
            plt.plot(dates, macd_most_expensive, label='MACD', color='blue')
            plt.plot(dates, signal_most_expensive, label='Signal', color='red')
            plt.bar(dates, histogram_most_expensive, label='Histograma', color='gray', alpha=0.5)
            plt.title(title_most_expensive)
            plt.xlabel('Data')
            plt.ylabel('MACD')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            # Exibir todos os gráficos
            st.pyplot(plt)
        else:
            st.warning('Por favor, digite um símbolo de criptomoeda válido.')

if __name__ == '__main__':
    main()
