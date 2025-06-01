import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def total_amount_invested(initial_amount, recurring_contribution, dates, frequency):
    """
    Calculates how much money was invested over time in total
    """
    # Maps the frequency to the number of months between contributions
    frequency_to_months = {
        "Mensuel": 1,      
        "Trimestriel": 3,   
        "Semestriel": 6,   
        "Annuel": 12       
    }
    
    months_gap = frequency_to_months[frequency]
    
    # Get the number of contributions made
    contribution_count = 0
    for i in range(1, len(dates)):
        if i % months_gap == 0:  # Check if it's time to contribute
            contribution_count += 1
    
    total_invested = initial_amount + (recurring_contribution * contribution_count)
    
    return total_invested


def get_portfolio_value(portfolio_values):
    """
    Get the last value from the portfolio
    """
    # Just return the last element in the list
    return portfolio_values[-1]


def calculate_annual_return_rate(amount_invested, final_portfolio_value, date_list):
    """
    Calculate CAGR (Compound Annual Growth Rate)
    
    CAGR formula: (Final Value / Initial Value)^(1/years) - 1
    """
    
    # Calculate the investment period was
    start_date = date_list[0]
    end_date = date_list[-1]
    time_difference = end_date - start_date
    years = time_difference.days / 365.25  # 365.25 accounts for leap years
    
    # If the investment period is 0 or negative, return 0
    if years <= 0:
        return 0
    
    # Apply CAGR formula
    cagr = (final_portfolio_value / amount_invested) ** (1 / years) - 1
    return cagr


def calculate_volatility(portfolio_values):
    """
    Calculate the standard volatility of returns
    """

    values_series = pd.Series(portfolio_values)
    
    # Calculate percentage change between consecutive values
    # pct_change() gives us the returns for each period
    returns = values_series.pct_change()
    
    # Remove NaN values (the first return will be NaN)
    clean_returns = returns.dropna()
    
    # If we have no returns, volatility is 0
    if clean_returns.empty:
        return 0
    
    # Multiply by sqrt(12) to convert monthly volatility to annual
    monthly_std = clean_returns.std()
    annual_volatility = monthly_std * np.sqrt(12)
    
    return annual_volatility

def calculate_sharpe_ratio(annual_return, volatility, risk_free_rate=0.02):
    """
    Calculate Sharpe Ratio, it measures return per unit of risk
    Formula: (Portfolio Return - Risk Free Rate) / Portfolio Volatility
    """

    # Avoid division by zero
    if volatility <= 0:
        return 0
    
    sharpe = (annual_return - risk_free_rate) / volatility
    return sharpe

def calculate_portfolio_metrics(portfolio_values, dates, portfolio):
    """
    Get all metrics
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
        "Valeur du portefeuille": f"{final_value:,.0f} €",
        "Cash non investi": f"{portfolio.cash_reserve:,.0f} €",
        "CAGR": f"{cagr * 100:.2f} %",
        "Volatilité annualisée": f"{volatility * 100:.2f} %",
        "Ratio de Sharpe": f"{sharpe_ratio:.2f}"
    }


def interpret_cagr(cagr_percentage):
    """
    Interprets CAGR (Compound Annual Growth Rate) percentage
    """
    if cagr_percentage < 0:
        return "Performance négative. Le portefeuille perd de la valeur en moyenne chaque année."
    elif cagr_percentage < 2:
        return "Rendement faible, proche des obligations d'État. Considérez une stratégie plus agressive."
    elif cagr_percentage < 5:
        return "Rendement modéré, typique d'un portefeuille conservateur ou d'obligations."
    elif cagr_percentage < 8:
        return "Bon rendement, dans la moyenne des marchés obligataires et actions mixtes."
    elif cagr_percentage < 12:
        return "Très bon rendement, proche de la moyenne historique des marchés actions."
    elif cagr_percentage < 20:
        return "Excellent rendement, supérieur à la moyenne des marchés. Performance remarquable."
    else:
        return "Rendement exceptionnel, mais attention au risque élevé associé."


def interpret_volatility(volatility_percentage):
    """
    Interprets annualized volatility percentage
    """
    if volatility_percentage < 5:
        return "Très faible volatilité. Portefeuille très stable, probablement conservateur."
    elif volatility_percentage < 10:
        return "Faible volatilité. Portefeuille relativement stable avec peu de fluctuations."
    elif volatility_percentage < 15:
        return "Volatilité modérée. Fluctuations normales pour un portefeuille équilibré."
    elif volatility_percentage < 20:
        return "Volatilité élevée. Portefeuille dynamique avec des fluctuations importantes."
    elif volatility_percentage < 30:
        return "Très haute volatilité. Portefeuille agressif avec de fortes variations."
    else:
        return "Volatilité extrême. Risque très élevé, adapté aux investisseurs expérimentés."


def interpret_sharpe_ratio(sharpe_ratio):
    """
    Interprets Sharpe ratio value
    """
    if sharpe_ratio < 0:
        return "Ratio négatif. Le portefeuille sous-performe par rapport au taux sans risque."
    elif sharpe_ratio < 0.5:
        return "Ratio faible. Rendement insuffisant par rapport au risque pris."
    elif sharpe_ratio < 1:
        return "Ratio acceptable. Compensation correcte du risque, mais améliorable."
    elif sharpe_ratio < 1.5:
        return "Bon ratio. Bonne compensation du risque pris, performance solide."
    elif sharpe_ratio < 2:
        return "Très bon ratio. Excellente compensation du risque, performance remarquable."
    else:
        return "Ratio exceptionnel. Performance ajustée au risque excellente."


def interpret_performance_vs_investment(final_value, amount_invested, date_list):
    """
    Interprets overall performance (gain/loss vs invested amount) considering time period
    """
    gain_loss = final_value - amount_invested
    performance_percentage = (gain_loss / amount_invested) * 100
    
    # Calculate investment period in years
    start_date = date_list[0]
    end_date = date_list[-1]
    time_difference = end_date - start_date
    years = time_difference.days / 365.25
    
    # Calculate annualized return for context
    if years > 0:
        annualized_return = (final_value / amount_invested) ** (1 / years) - 1
        annualized_percentage = annualized_return * 100
    else:
        annualized_percentage = 0
    
    # Interpret based on total return and time context
    if performance_percentage < -20:
        return f"Perte importante de {performance_percentage:.1f}% sur {years:.1f} ans. Réévaluez votre stratégie d'investissement."
    elif performance_percentage < -10:
        return f"Perte modérée de {performance_percentage:.1f}% sur {years:.1f} ans. Situation temporaire ou stratégie à ajuster."
    elif performance_percentage < 0:
        return f"Légère perte de {performance_percentage:.1f}% sur {years:.1f} ans. Performance en deçà des attentes."
    elif years < 1:
        # For periods less than 1 year, focus on absolute performance
        if performance_percentage < 5:
            return f"Gain modeste de {performance_percentage:.1f}% sur {years*12:.0f} mois. Début prometteur."
        elif performance_percentage < 15:
            return f"Bon gain de {performance_percentage:.1f}% sur {years*12:.0f} mois. Performance solide à court terme."
        else:
            return f"Excellent gain de {performance_percentage:.1f}% sur {years*12:.0f} mois. Performance remarquable."
    else:
        # For periods over 1 year, consider annualized performance
        if annualized_percentage < 3:
            return f"Gain total de {performance_percentage:.1f}% sur {years:.1f} ans ({annualized_percentage:.1f}% annualisé). Performance conservatrice."
        elif annualized_percentage < 7:
            return f"Gain total de {performance_percentage:.1f}% sur {years:.1f} ans ({annualized_percentage:.1f}% annualisé). Performance satisfaisante."
        elif annualized_percentage < 12:
            return f"Gain total de {performance_percentage:.1f}% sur {years:.1f} ans ({annualized_percentage:.1f}% annualisé). Très bonne performance."
        else:
            return f"Gain total de {performance_percentage:.1f}% sur {years:.1f} ans ({annualized_percentage:.1f}% annualisé). Performance exceptionnelle."


def interpret_cash_reserve(cash_reserve, total_portfolio_value):
    """
    Interprets the uninvested cash reserve
    """
    if cash_reserve <= 0:
        return "Aucune réserve de liquidités. Portefeuille entièrement investi."
    
    cash_percentage = (cash_reserve / total_portfolio_value) * 100
    
    if cash_percentage < 5:
        return f"{cash_percentage:.1f}% en liquidités. Réserve minimale, portefeuille très investi."
    elif cash_percentage < 10:
        return f"{cash_percentage:.1f}% en liquidités. Réserve raisonnable pour les opportunités."
    elif cash_percentage < 20:
        return f"{cash_percentage:.1f}% en liquidités. Bonne réserve de sécurité et d'opportunités."
    elif cash_percentage < 30:
        return f"{cash_percentage:.1f}% en liquidités. Réserve importante, peut-être sous-optimale."
    else:
        return f"{cash_percentage:.1f}% en liquidités. Réserve très élevée, manque d'opportunités d'investissement."


def get_all_interpretations(metrics_dict, date_list):
    """
    Generates all interpretations from the metrics dictionary
    """
    # Extract numeric values from formatted strings
    amount_invested = float(metrics_dict["Montant investi"].replace(" €", "").replace(",", ""))
    final_value = float(metrics_dict["Valeur du portefeuille"].replace(" €", "").replace(",", ""))
    cash_reserve = float(metrics_dict["Cash non investi"].replace(" €", "").replace(",", ""))
    cagr = float(metrics_dict["CAGR"].replace(" %", ""))
    volatility = float(metrics_dict["Volatilité annualisée"].replace(" %", ""))
    sharpe_ratio = float(metrics_dict["Ratio de Sharpe"])
    
    interpretations = {
        "Montant investi": f"Capital total: {amount_invested:,.0f}€ déployé sur la période d'investissement.",
        "Valeur du portefeuille": interpret_performance_vs_investment(final_value, amount_invested, date_list),
        "Cash non investi": interpret_cash_reserve(cash_reserve, final_value + cash_reserve),
        "CAGR": interpret_cagr(cagr),
        "Volatilité annualisée": interpret_volatility(volatility),
        "Ratio de Sharpe": interpret_sharpe_ratio(sharpe_ratio)
    }
    
    return interpretations


def get_metrics_with_interpretations(portfolio_values, dates, portfolio):
    """
    Calculates metrics with their interpretations
    """
    from metrics import calculate_portfolio_metrics
    
    # Calculate base metrics
    metrics = calculate_portfolio_metrics(portfolio_values, dates, portfolio)
    
    # Add interpretations (now includes date context)
    interpretations = get_all_interpretations(metrics, dates)
    
    # Combine metrics and interpretations
    result = {}
    for key in metrics.keys():
        result[key] = {
            "value": metrics[key],
            "interpretation": interpretations[key]
        }
    
    return result