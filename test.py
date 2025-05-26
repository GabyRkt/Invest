from portfolio import Portfolio, Asset
from utils import get_etf_info
from simulation import InvestmentSimulator, compute_metrics
import plotly.express as px
import datetime as datetime

weights = {"IWDA.AS": 70, "AGGH.AS": 30}

assets = [
    Asset(ticker, weight, fee=get_etf_info(ticker)["fees"])
    for ticker, weight in weights.items()
]

# Define investment period in mm/YYYY
start_date = "01/2023"
end_date = "08/2024"

portfolio = Portfolio(
    assets=assets,
    initial_amount=10000,
    recurring_contribution=500,
    contribution_frequency="Mensuel",
    start_date=start_date,
    end_date=end_date,
    service_fee=0.2
)

simulator = InvestmentSimulator(portfolio)
df = simulator.simulate()

metrics = compute_metrics(
    portfolio_values=df["Portfolio Value"].values,
    dates=df.index.to_list(),
    initial_amount=portfolio.initial_amount,
    recurring_contribution=portfolio.recurring_contribution,
    contribution_freq=portfolio.contribution_frequency
)

# === Display Results ===
print("\n📊 Résumé de la performance:")
print(f"Montant investi : {metrics['invested']:.2f} €")
print(f"Valeur finale   : {metrics['final_value']:.2f} €")
print(f"CAGR            : {metrics['cagr']*100:.2f} %")
print(f"Écart-type      : {metrics['std_dev']*100:.2f} %")
print(f"Ratio de Sharpe : {metrics['sharpe_ratio']:.2f}")

# === Plot Portfolio Evolution ===
fig = px.line(
    df.reset_index(),
    x="Date",
    y="Portfolio Value",
    title="Évolution du portefeuille"
)

fig.update_traces(
    hovertemplate="%{x|%b %Y}<br>Valeur : %{y:,.0f} €"
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Valeur (€)",
    xaxis_tickformat="%b %Y"
)

fig.show()


fig.show()
 #### PROBLEME : ON NE DEBUTE PAS A 10K, WHY ? 