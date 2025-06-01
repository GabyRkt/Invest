from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import json
from portfolio import Portfolio, Asset
from etf_search import search_etfs
from simulation import InvestmentSimulator, plot_portfolio, get_invested_amount, plot_annual_returns, interpret_annual_returns
from metrics import total_amount_invested, get_portfolio_value, calculate_annual_return_rate, calculate_volatility, calculate_sharpe_ratio, get_metrics_with_interpretations
from regression import regression, plot_regression
from comparison import simulate_acwi_equivalent, compare_user_vs_acwi

# Flask app configuration
app = Flask(__name__)
app.secret_key = 'secret_for_session'


@app.route('/search_etfs')
def search_etfs_route():
    """
    API enpoint to search for ETFs
    """

    q = request.args.get('q', '')
    return jsonify(search_etfs(q))


def get_form_defaults():
    """
    Get default form values for the portfolio configuration
    """
    current_date = datetime.today()
    return {
        'initial_amount': '',
        'recurring_contribution': '',
        'frequency': 'Mensuel',
        'start_month': '',
        'start_year': '',
        'end_month': '',
        'end_year': '',
        'fee': '',
        'tickers': '[]',
        'allocations': '{}',
        'current_year': current_date.year,
        'previous_month': 12 if current_date.month == 1 else current_date.month - 1
    }

def create_portfolio_from_session_data(form_data):
    """
    Create a Portfolio object data
    """
    
    assets = [
        Asset(ticker, float(form_data['allocations'][ticker])) 
        for ticker in form_data['tickers']
    ]

    return Portfolio(
        assets=assets,
        initial_amount=float(form_data['initial_amount']),
        recurring_contribution=float(form_data['recurring_contribution']),
        contribution_frequency=form_data['frequency'],
        start_date=datetime.strptime(form_data['start_date'], "%Y-%m-%d"),
        end_date=datetime.strptime(form_data['end_date'], "%Y-%m-%d"),
        service_fee=float(form_data['fee'])
    )


def validate_form_data(form):
    """
    Validate and parse form data for portfolio creation
    """
    
    # Parse and validate numeric inputs
    try:
        initial = float(form['initial_amount'].strip())
        recurring = float(form['recurring_contribution'].strip())
        fee = float(form.get('fee', 0).strip() or 0)
    except (ValueError, TypeError):
        raise ValueError("Valeurs numériques invalides.")

    # Validate ranges
    if initial < 0:
        raise ValueError("Montant initial invalide.")
    if recurring < 0:
        raise ValueError("Contribution récurrente invalide.")
    if not (0 <= fee <= 100):
        raise ValueError("Frais hors limites (0-100%).")

    # Parse dates
    try:
        start_date = datetime(int(form['start_year']), int(form['start_month']), 1)
        end_date = datetime(int(form['end_year']), int(form['end_month']), 1)
    except (ValueError, TypeError):
        raise ValueError("Dates invalides.")

    # Validate date 
    today = datetime.today().replace(day=1)
    if end_date >= today:
        raise ValueError("Date de fin dans le futur.")
    if end_date <= start_date:
        raise ValueError("Date de fin avant début.")

    # Parse and validate portfolio composition
    try:
        tickers = json.loads(form.get('tickers', '[]'))
        allocations = json.loads(form.get('allocations', '{}'))
    except json.JSONDecodeError:
        raise ValueError("Format de portefeuille invalide.")

    if not tickers:
        raise ValueError("Aucun ETF sélectionné.")
    
    total_allocation = sum(float(allocations.get(ticker, 0)) for ticker in tickers)
    if total_allocation == 0:
        raise ValueError("Aucune allocation définie.")
    if total_allocation > 100:
        raise ValueError(f"Allocation totale ({total_allocation:.1f}%) dépasse 100%.")

    return {
        'initial_amount': initial,
        'recurring_contribution': recurring,
        'frequency': form['frequency'],
        'start_date': start_date,
        'end_date': end_date,
        'fee': fee,
        'tickers': tickers,
        'allocations': allocations
    }


def calculate_portfolio_metrics(portfolio_values, dates, portfolio):
    """
    Calculate comprehensive portfolio performance metrics
    """
    invested = total_amount_invested(
        portfolio.initial_amount, 
        portfolio.recurring_contribution, 
        dates, 
        portfolio.contribution_frequency
    )
    final_value = get_portfolio_value(portfolio_values)
    cagr = calculate_annual_return_rate(invested, final_value, dates)
    volatility = calculate_volatility(portfolio_values)
    sharpe_ratio = calculate_sharpe_ratio(cagr, volatility)

    return {
        "Montant investi": f"{invested:,.0f} €",
        "Valeur finale": f"{final_value:,.0f} €",
        "CAGR": f"{cagr * 100:.2f} %",
        "Volatilité annualisée": f"{volatility * 100:.2f} %",
        "Ratio de Sharpe": f"{sharpe_ratio:.2f}"
    }


def perform_regression_analysis(df, scale='linear'):
    """
    Perform regression analysis on portfolio performance
    """
    reg_result = regression(df.index.to_list(), df["Portfolio Value"].values, scale=scale)
    regression_graph = plot_regression(df, scale=scale)
    
    regression_analysis = {
        "Facteur de corrélation (R²)": f"{reg_result['r2']:.4f}",
        "Distance au modèle (en %)": f"{reg_result['diff_percent']:.2f} %",
        "Écart-type des résidus": f"{reg_result['residual_std']:.4f} %",
        "Position du dernier point (×σ)": f"{reg_result['diff_std']:.2f} σ"
    }
    
    return regression_graph, regression_analysis

def perform_acwi_comparison(portfolio, user_df):
    """
    Compare user portfolio performance with ACWI benchmark
    """

    # Simulate equivalent ACWI investment
    acwi_df = simulate_acwi_equivalent(portfolio)
    acwi_values = acwi_df["Portfolio Value"].values
    acwi_dates = acwi_df.index.to_list()

    # Calculate ACWI metrics
    acwi_invested = total_amount_invested(
        portfolio.initial_amount, 
        portfolio.recurring_contribution, 
        acwi_dates, 
        portfolio.contribution_frequency
    )
    acwi_final = get_portfolio_value(acwi_values)
    acwi_cagr = calculate_annual_return_rate(acwi_invested, acwi_final, acwi_dates)
    acwi_volatility = calculate_volatility(acwi_values)
    acwi_sharpe = calculate_sharpe_ratio(acwi_cagr, acwi_volatility)

    # Calculate user metrics for comparison
    user_values = user_df["Portfolio Value"].values
    user_dates = user_df.index.to_list()
    user_invested = total_amount_invested(
        portfolio.initial_amount, 
        portfolio.recurring_contribution, 
        user_dates, 
        portfolio.contribution_frequency
    )
    user_final = get_portfolio_value(user_values)
    user_cagr = calculate_annual_return_rate(user_invested, user_final, user_dates)
    user_volatility = calculate_volatility(user_values)
    user_sharpe = calculate_sharpe_ratio(user_cagr, user_volatility)

    # Format comparison metrics
    comparison_metrics = {
        "Montant investi": {
            "Vous": f"{user_invested:,.0f} €", 
            "ACWI": f"{acwi_invested:,.0f} €"
        },
        "Valeur finale": {
            "Vous": f"{user_final:,.0f} €", 
            "ACWI": f"{acwi_final:,.0f} €"
        },
        "CAGR": {
            "Vous": f"{user_cagr * 100:.2f} %", 
            "ACWI": f"{acwi_cagr * 100:.2f} %"
        },
        "Volatilité annualisée": {
            "Vous": f"{user_volatility * 100:.2f} %", 
            "ACWI": f"{acwi_volatility * 100:.2f} %"
        },
        "Ratio de Sharpe": {
            "Vous": f"{user_sharpe:.2f}", 
            "ACWI": f"{acwi_sharpe:.2f}"
        }
    }

    comparison_graph = compare_user_vs_acwi(user_df, acwi_df)
    
    return comparison_metrics, comparison_graph


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handling portfolio simulation and analysis
    """
    # Initialize context with default values
    form_defaults = get_form_defaults()
    context = {
        'form_data': form_defaults.copy(),
        'portfolio': None,
        'error': None,
        'current_year': form_defaults['current_year'],
        'previous_month': form_defaults['previous_month']
    }

    # Handle form submission
    if request.method == 'POST':
        try:
            
            validated_data = validate_form_data(request.form)
            session['form_data'] = {
                **validated_data,
                'start_date': validated_data['start_date'].strftime('%Y-%m-%d'),
                'end_date': validated_data['end_date'].strftime('%Y-%m-%d')
            }

            # Redirect to GET to prevent form resubmission
            return redirect(url_for('index'))

        except Exception as e:
            context['error'] = str(e)
            context['form_data'].update(request.form)
            return render_template('index.html', **context)

    # Process existing portfolio data 
    form_data = session.get('form_data')
    if form_data:
        try:
            # Create portfolio and run simulation
            portfolio = create_portfolio_from_session_data(form_data)
            simulator = InvestmentSimulator(portfolio)
            df = simulator.simulate()

            # Calculate invested amount over time
            invested_amount = get_invested_amount(
                dates=df.index.to_list(),
                initial_amount=portfolio.initial_amount,
                recurring_contribution=portfolio.recurring_contribution,
                frequency=portfolio.contribution_frequency
            )

            # Get chart scaling preferences
            scale = request.args.get('scale', 'linear')
            reg_scale = request.args.get('reg_scale', 'linear')

            # Generate main portfolio chart
            graph = plot_portfolio(df, scale=scale, invested_amount=invested_amount)

            # Calculate portfolio performance metrics
            portfolio_values = df["Portfolio Value"].values
            dates = df.index.to_list()
            metrics = get_metrics_with_interpretations(portfolio_values, dates, portfolio)


            # Perform regression analysis
            regression_graph, regression_analysis = perform_regression_analysis(df, reg_scale)

            # Compare with ACWI benchmark
            comparison_metrics, comparison_graph = perform_acwi_comparison(portfolio, df)

            # Get annual returns chart
            annual_returns_chart = plot_annual_returns(df)
            annual_returns_interpretation = interpret_annual_returns(df)

            # Update context with analysis results
            context.update({
                'portfolio': portfolio,
                'portfolio_data': portfolio.print_summary(),
                'graph_html': graph,
                'metrics': metrics,
                'regression_graph': regression_graph,
                'regression_analysis': regression_analysis,
                'comparison_metrics': comparison_metrics,
                'comparison_graph': comparison_graph,
                'scale': scale,
                'reg_scale': reg_scale, 
                'annual_returns_chart': annual_returns_chart, 'annual_returns_interpretation': annual_returns_interpretation
            })



        except Exception as e:
            context['error'] = f"Erreur lors de l'analyse du portefeuille: {str(e)}"

    return render_template('index.html', **context)


if __name__ == '__main__':
    app.run(debug=True)


