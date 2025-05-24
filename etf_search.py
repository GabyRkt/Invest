import csv

def load_etfs(csv_path='etfs.csv'):
    etfs = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            etfs.append({'symbol': row['symbol'].upper(), 'name': row['name']})
    return etfs

ETFS = load_etfs()

def search_etfs(query):
    query = query.upper()
    if len(query) < 1: #dès que je mets un caractère je peux faire la recherche
        return []
    results = [etf for etf in ETFS if etf['symbol'].startswith(query)]
    return results
