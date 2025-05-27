from flask import Flask, render_template, request, jsonify
from datetime import datetime
from portfolio import Portfolio, Asset
from etf_search import search_etfs
import json

app = Flask(__name__)

@app.route('/search_etfs')
def search_etfs_route():
    q = request.args.get('q', '')
    results = search_etfs(q)
    return jsonify(results) # To simplify, we return a list of dict {symbol, name}

@app.route('/', methods=['GET', 'POST'])
def index():

    current_month = datetime.today().month # get the current month
    previous_month = 12 if current_month == 1 else current_month - 1 # get the month before the current month
    current_year = datetime.today().year 

    form_defaults = {
        'initial_amount': '',
        'recurring_contribution': '',
        'frequency': 'Mensuel',
        'start_month': '',
        'start_year': '',
        'end_month': '',
        'end_year': '',
        'fee': '',
        'tickers': '[]',
        'allocations': '{}'
    }

    context = {
        'form_data': form_defaults.copy(),
        'portfolio': None,
        'error': None
    }

    if request.method == 'POST':
        try:
            form = request.form

            # ---- Validate amounts ----
            initial_amount = float(form['initial_amount'])
            if initial_amount < 0:
                raise ValueError("Entrez un montant.")

            recurring_contrib = float(form['recurring_contrib'])
            if recurring_contrib <= 0:
                raise ValueError("Les montants doivent être positifs.")
            
            # ---- Validate dates ----
            frequency = form['frequency']
            start_month = int(form['start_month'])
            start_year = int(form['start_year'])
            end_month = int(form['end_month'])
            end_year = int(form['end_year'])

            start_date = datetime(start_year, start_month, 1)
            end_date = datetime(end_year, end_month, 1)
            today = datetime.today().replace(day=1)

            if end_date >= today:
                raise ValueError("La date de fin doit être avant le mois actuel.")
            if end_date <= start_date:
                raise ValueError("La date de fin doit être après la date de début.")
            
            # ---- Validate service fee ----
            fee = float(form['fee']) if form['fee'] else 0.0
            if not 0 <= fee <= 100:
                raise ValueError("Les frais doivent être entre 0 et 100 %.")

            # ---- Read ETF and allocations ----
            tickers_raw = form.get('tickers', '[]')
            allocations_raw = form.get('allocations', '{}')
            tickers = json.loads(tickers_raw)
            allocations = json.loads(allocations_raw)

            # Validate ETF selection
            if not tickers:
                raise ValueError("Veuillez sélectionner au moins un ETF.")

            # ---- Validate allocation and create assets ----
            assets = [Asset(ticker=t, weight=float(allocations.get(t, 0))) for t in tickers]
            if assets:
                total_allocation = sum(asset.weight for asset in assets)
                if round(total_allocation, 2) != 100.0:
                    raise ValueError("La somme des allocations des ETF doit faire 100 %.")

            # ---- Build porfolio ----
            portfolio = Portfolio(
                initial_amount=initial_amount,
                recurring_contribution=recurring_contrib,
                contribution_frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                service_fee=fee,
                assets=assets
            )

            # ---- Update context for template ----
            context['portfolio'] = portfolio

            # Update form_data with inputs value to keep it displayed in the form
            context['form_data'] = form_defaults.copy()
            context['form_data'].update(form)

        except Exception as e:
            context['error'] = str(e)
            # We keep the values even if there's an error
            context['form_data'] = form_defaults.copy()
            context['form_data'].update(request.form)


    return render_template('index.html', **context, current_year=current_year,previous_month=previous_month)

if __name__ == '__main__':
    app.run(debug=True)
