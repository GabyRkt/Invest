import pandas as pd

def compute_metrics(portfolio_values, dates, initial_amount, recurring_contribution, contribution_freq):

    # 🟢 Get the final value of the portfolio (last simulated month)
    final_value = portfolio_values[-1]

    # 🟢 Frequency map: convert frequency string (in French) into # of months between contributions
    freq_map = {
        "Mensuel": 1,
        "Trimestriel": 3,
        "Semestriel": 6,
        "Annuel": 12
    }
    months_between_contribs = freq_map[contribution_freq]  # e.g. 'Mensuel' → 1

    # 🧮 Count how many contributions were made (excluding the initial investment)
    num_contributions = sum(1 for i in range(1, len(dates)) if i % months_between_contribs == 0)

    # 🟢 Total invested = initial amount + all recurring contributions
    invested = initial_amount + recurring_contribution * num_contributions

    # 🧮 Calculate the investment duration in years
    years = (dates[-1] - dates[0]).days / 365.25  # approximate year fraction

    # 📈 CAGR: Compound Annual Growth Rate
    if invested > 0:
        cagr = (final_value / invested) ** (1 / years) - 1
    else:
        cagr = 0

    # 📊 Compute monthly returns from portfolio values
    monthly_returns = pd.Series(portfolio_values).pct_change().dropna()

    # 📉 Annualized volatility (standard deviation) from monthly returns
    std_dev = monthly_returns.std() * np.sqrt(12)

    # ⚖️ Sharpe Ratio: risk-adjusted return using risk-free rate (2% by default)
    risk_free_rate = 0.02
    if std_dev > 0:
        sharpe_ratio = (cagr - risk_free_rate) / std_dev
    else:
        sharpe_ratio = 0  # Avoid division by zero

    # 🧾 Return all computed metrics in a dictionary
    return {
        "invested": invested,              # Total invested capital
        "final_value": final_value,        # Final portfolio value
        "cagr": cagr,                      # Annual growth rate
        "std_dev": std_dev,                # Volatility
        "sharpe_ratio": sharpe_ratio       # Risk-adjusted performance
    }
