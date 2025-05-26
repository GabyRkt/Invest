import yfinance as yf

def get_etf_info(ticker_symbol):
    try:
        info = yf.Ticker(ticker_symbol).info
        return {'fees': info.get('netExpenseRatio', 0.0), 'ticker': ticker_symbol}
    except:
        return {'fees': 0.0, 'ticker': ticker_symbol}
