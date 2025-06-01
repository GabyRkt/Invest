import pandas as pd
import numpy as np
import yfinance as yf
from simulation import InvestmentSimulator
from portfolio import Portfolio, Asset
import plotly.express as px
import plotly.graph_objects as go

def get_monthly_prices(ticker, start_date, end_date):
    """
    This function downloads daily price data  of a ticker and resamples it to monthly frequency
    It uses the last trading day of each month as the monthly price
    """
    data = yf.download(
        ticker,
        start=start_date - pd.DateOffset(months=1),
        end=end_date,
        interval="1d",
        auto_adjust=True
    )["Close"]

    # Resample to monthly frequency using last trading day of each month
    monthly = data.resample('ME').last()

    monthly.index = monthly.index + pd.offsets.MonthBegin(1)
    return monthly


def simulate_acwi_equivalent(portfolio_user):
    """
    Create and simulate an ACWI portfolio equivalent to a user's portfolio
    """
    
    # First, get ACWI data to find the first available date
    acwi_prices = get_monthly_prices("ACWI", portfolio_user.start_date, portfolio_user.end_date)
    acwi_first_date = acwi_prices.first_valid_index()
    
    # Use ACWI first available date or user's start date, whichever is later
    effective_start_date = max(portfolio_user.start_date, acwi_first_date) if acwi_first_date else portfolio_user.start_date
    
    # Create ACWI asset with 100% allocation
    acwi_asset = Asset("ACWI", 100.0)  

    acwi_portfolio = Portfolio(
        assets=[acwi_asset],
        initial_amount=portfolio_user.initial_amount,
        recurring_contribution=portfolio_user.recurring_contribution,
        contribution_frequency=portfolio_user.contribution_frequency,
        start_date=effective_start_date,  # Use adjusted start date
        end_date=portfolio_user.end_date,
        service_fee=portfolio_user.service_fee
    )

    simulator = InvestmentSimulator(acwi_portfolio)
    df_acwi = simulator.simulate()

    return df_acwi


def compare_user_vs_acwi(user_df, acwi_df):
    """
    Generate comparison chart between user portfolio and ACWI benchmark
    """

    # Create new Plotly figure
    fig = go.Figure()

    # Add user portfolio line (1st line)
    fig.add_trace(go.Scatter(
        x=user_df.index,
        y=user_df["Portfolio Value"],
        mode="lines",
        name="Votre portefeuille",
        line=dict(color="blue"),
        hovertemplate="%{y:,.0f} €<extra></extra>"
    ))

     # Add ACWI benchmark line (reference line)
    fig.add_trace(go.Scatter(
        x=acwi_df.index,
        y=acwi_df["Portfolio Value"],
        mode="lines",
        name="ACWI (référence)",
        line=dict(color="green", dash="dot"),
        hovertemplate="ACWI : %{y:,.0f} €<extra></extra>"
    ))

    # Configure chart layout 
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        xaxis_tickformat="%b %Y",   # Format: Jan 2020
        hovermode="x unified",      # Show both values on same hover
        legend_title="Légende"
    )

    return fig.to_html(full_html=False)