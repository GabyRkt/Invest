import csv
import yfinance as yf

def load_etfs(csv_path='etfs.csv'):
    """
    Load ETF data from a CSV file
    """
    etfs = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                etfs.append({'symbol': row['symbol'].upper(), 'name': row['name']})
    
    except FileNotFoundError:
        print(f"Warning: CSV file '{csv_path}' not found. ETF list will be empty.")
    except Exception as e:
        print(f"Error loading ETF data: {e}")

    return etfs


# Load ETFs once at module import time for better performance
ETFS = load_etfs()


def search_etfs(query):
    """
    Search for ETFs whose symbols start with the input
    """
    query = query.upper()
    
    if len(query) < 1: # minimum 1 character
        return []
    
    # Filter ETFs where symbol starts with the input
    results = [etf for etf in ETFS if etf['symbol'].startswith(query)]
    
    return results


def get_etf_name(symbol):
    """
    Get the full name of an ETF using its symbol
    """

    symbol = symbol.upper()
    for etf in ETFS:
        if etf['symbol'] == symbol:
            return etf['name']
        
    return symbol 


def get_etf_info(ticker_symbol):
    try:
        info = yf.Ticker(ticker_symbol).info
        return {'fees': info.get('netExpenseRatio', 0.0), 'ticker': ticker_symbol}
    except:
        return {'fees': 0.0, 'ticker': ticker_symbol}