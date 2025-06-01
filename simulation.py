import pandas as pd
import numpy as np
import yfinance as yf
from portfolio import Portfolio
from etf_search import get_etf_info
import plotly.express as px
import plotly.graph_objects as go


class InvestmentSimulator:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio

        # Mapping of contribution frequency to number of months between contributions
        self.freq_map = {"Mensuel": 1, "Trimestriel": 3, "Semestriel": 6, "Annuel": 12}
        self.months_between_contributions = self.freq_map[portfolio.contribution_frequency]
        
        # Generate list of monthly dates from start to end (1st day of each month)
        self.dates = pd.date_range(start=portfolio.start_date, end=portfolio.end_date, freq='MS') # MS for the first day of the month

        # Get ETF tickers and weights from the portfolio
        self.tickers = [etf.ticker for etf in portfolio.assets]
        self.weights = np.array([etf.weight for etf in portfolio.assets])

        self.data = self._load_data()



    def _load_data(self):
        """
        Loads historical closing prices, per month.
        For a month, the price is of the last day of last's month.
        Ex. for may 2024, we have the closing price of april 30th, 2024.
        """

        # Download daily price data from yfinance
        # Starting one month earlier to get last month's close
        data = yf.download(
            self.tickers,
            start=self.portfolio.start_date - pd.DateOffset(months=1), # starting one month earlier 
            end=self.portfolio.end_date,
            interval="1d",  # daily to get the last day of the month
            auto_adjust=True)["Close"]

        # If only one instance of ticker, dataframe structure instead of series
        if isinstance(data, pd.Series):
            data = data.to_frame()

        # Get the last available price of each month
        monthly_data = data.resample('ME').last()
      
        # Assign each price of the last day of the month to the 1st of the next month
        monthly_data.index = monthly_data.index + pd.offsets.MonthBegin(1)

        # Align with expected simulation dates (already using 'M')
        return monthly_data.reindex(self.dates, method='ffill')


    def simulate(self):
        '''
        Simulate passive ETF investing
        '''
        
        # Get ETF expense ratios
        etf_expense_ratios = {}
        for ticker in self.tickers:
            etf_info = get_etf_info(ticker)
            etf_expense_ratios[ticker] = etf_info['fees']
        
        
        
        # Determine first valid date for each ETF
        first_available_dates = {
            ticker: date for ticker in self.tickers
            if (date := self.data[ticker].first_valid_index()) is not None
        }
        
        # Get available ETFs at a given date
        def get_available_etfs(date):
            available_etfs = []
            for etf in self.portfolio.assets:
                if (etf.ticker in first_available_dates and 
                    first_available_dates[etf.ticker] <= date):
                    available_etfs.append(etf)
            return available_etfs
        
        # Calculate dynamic weights
        def get_dynamic_weights(date):
            available_etfs = get_available_etfs(date)
            if not available_etfs:
                return {}
            
            # Calculate total weight of available ETFs
            total_available_weight = sum(etf.weight for etf in available_etfs)
            
            
            dynamic_weights = {}
            for etf in available_etfs:
                dynamic_weights[etf.ticker] = etf.weight / total_available_weight
                
            return dynamic_weights
        
        # Initial investment
        initial_date = self.dates[0]
        available_etfs_initial = get_available_etfs(initial_date)
        dynamic_weights_initial = get_dynamic_weights(initial_date)
        
        # print(f"Initial date: {initial_date}")
        # print(f"Available ETFs: {[etf.ticker for etf in available_etfs_initial]}")
        # print(f"Dynamic weights: {dynamic_weights_initial}")
        
        first_prices = self.data.loc[initial_date]
        
        # Initial investment (only in available ETFs)
        for etf in available_etfs_initial:
            ticker = etf.ticker
            price = first_prices[ticker]
            if np.isnan(price):
                continue
            
            # Use dynamic weight instead of original weight
            allocation_amount = self.portfolio.initial_amount * dynamic_weights_initial[ticker]
            units = np.floor(allocation_amount / price)
            amount_used = units * price
            etf.units += units
            self.portfolio.cash_reserve += allocation_amount - amount_used
        
        portfolio_values = []
        monthly_fee_rate = self.portfolio.service_fee / 100 / 12

        # Convert annual ETF expense ratios to daily rates ( ~252 trading days per year)
        daily_etf_expense_rates = {
            ticker: expense_ratio / 252 for ticker, expense_ratio in etf_expense_ratios.items()
        }
        
        # Keep track of previous available ETFs to detect when new ones become available
        prev_available_tickers = set(etf.ticker for etf in available_etfs_initial)
        
        # Simulation loop
        for i, date in enumerate(self.dates):
            current_prices = self.data.loc[date]
            
            # Check if new ETFs became available
            current_available_etfs = get_available_etfs(date)
            current_available_tickers = set(etf.ticker for etf in current_available_etfs)
            
            # If new ETFs became available, rebalance the portfolio
            newly_available_tickers = current_available_tickers - prev_available_tickers
            if newly_available_tickers:
                print(f"Date {date}: New ETFs became available: {newly_available_tickers}")
                
                # Calculate current portfolio value
                current_portfolio_value = sum(
                    etf.units * current_prices[etf.ticker] 
                    for etf in self.portfolio.assets 
                    if etf.units > 0
                )
                total_value = current_portfolio_value + self.portfolio.cash_reserve
                
                # Sell all current holdings (prepare for reallocation)
                for etf in self.portfolio.assets:
                    if etf.units > 0:
                        self.portfolio.cash_reserve += etf.units * current_prices[etf.ticker]
                        etf.units = 0
                
                # Reinvest using new dynamic weights
                dynamic_weights_current = get_dynamic_weights(date)
                for etf in current_available_etfs:
                    ticker = etf.ticker
                    price = current_prices[ticker]
                    if np.isnan(price):
                        continue
                    
                    allocation_amount = total_value * dynamic_weights_current[ticker]
                    units = np.floor(allocation_amount / price)
                    amount_used = units * price
                    etf.units += units
                    self.portfolio.cash_reserve -= amount_used
            
            # Recurring contributions
            if i % self.months_between_contributions == 0 and i > 0:
                self.portfolio.cash_reserve += self.portfolio.recurring_contribution
                
                dynamic_weights_current = get_dynamic_weights(date)
                for etf in current_available_etfs:
                    ticker = etf.ticker
                    allocation_amount = dynamic_weights_current[ticker] * self.portfolio.cash_reserve
                    price = current_prices[ticker]
                    if np.isnan(price):
                        continue
                        
                    units_to_buy = np.floor(allocation_amount / price)
                    amount_used = units_to_buy * price
                    
                    etf.units += units_to_buy
                    self.portfolio.cash_reserve -= amount_used
            
            
            portfolio_value = 0

            # Apply daily ETF expense ratios to each holding individually
            for etf in self.portfolio.assets:
                if etf.units > 0:
                    ticker = etf.ticker
                    current_price = current_prices[ticker]
                    if np.isnan(current_price):
                        continue
                    
                    # Calculate value of this ETF holding
                    etf_value = etf.units * current_price
                    
                    # Apply daily ETF expense ratio (reduces the effective value)
                    if i > 0:  # Don't apply fees on the first day
                        daily_fee_rate = daily_etf_expense_rates.get(ticker, 0)
                        etf_value *= (1 - daily_fee_rate)
                    
                    portfolio_value += etf_value
            
            # Add cash reserve
            portfolio_value += self.portfolio.cash_reserve
            
            # Apply service fee only after the first month
            if i > 0:
                portfolio_value *= (1 - monthly_fee_rate)
            
            portfolio_values.append(portfolio_value)
            
            # Update previous available tickers
            prev_available_tickers = current_available_tickers
        
        # Create a dataframe with the portfolio values
        result_df = pd.DataFrame({
            "Date": self.dates,
            "Portfolio Value": portfolio_values
        }).set_index("Date")
        
        return result_df


def plot_portfolio(df, scale='linear', invested_amount=None):
    fig = go.Figure()

    # Line 1: Portfolio Value
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Portfolio Value"],
        mode="lines",
        name="Valeur du portefeuille",
        line=dict(color="blue"),
        hovertemplate="%{y:,.0f} €"
    ))

    # Line 2: Invested Amount
    if invested_amount is not None:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=invested_amount,
            mode="lines",
            name="Montant investi (cumulé)",
            line=dict(color="gray", dash="dash"),
            hovertemplate="%{y:,.0f} €"
        ))

    # Unified hover and vertical line
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        yaxis_type=scale,
        hovermode="x unified",
    )

    return fig.to_html(full_html=False)



def get_invested_amount(dates, initial_amount, recurring_contribution, frequency):
    """
    Calculate the total amount invested over time based on frequency
    """
    freq_map = {"Mensuel": 1, "Trimestriel": 3, "Semestriel": 6, "Annuel": 12}
    months_between = freq_map[frequency]

    invested = []
    total = initial_amount

    for i in range(len(dates)):
        if i != 0 and i % months_between == 0:
            total += recurring_contribution
        invested.append(total)

    return invested


def plot_annual_returns(df):
    """
     Generate a chart of annual returns in % from monthly portfolio values
    """
    # Calculate monthly returns
    monthly_returns = df["Portfolio Value"].pct_change()

    # Calculate compound annual returns
    annual_returns = ((1 + monthly_returns).resample("Y").prod() - 1) * 100
    years = annual_returns.index.year
    returns = annual_returns.values

    # Assign colors based on return sign
    colors = ["seagreen" if r >= 0 else "indianred" for r in returns]

    # Bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=returns,
        marker_color=colors,
        hovertemplate="%{y:.2f} %",
        name="Rendement annuel"
    ))

    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Rendement (%)",
        template="plotly_white",
        yaxis_ticksuffix=" %",
        hovermode="x unified"
    )

    return fig.to_html(full_html=False)


def interpret_annual_returns(df):
    """
    Generate a textual interpretation of the portfolio's annual returns   
    """

    # Calculate monthly and annual returns
    monthly_returns = df["Portfolio Value"].pct_change()
    annual_returns = ((1 + monthly_returns).resample("Y").prod() - 1) * 100
    annual_returns.index = annual_returns.index.year

    # Check data availability
    if annual_returns.empty:
        return "Aucune donnée disponible pour interpréter les rendements annuels."

    # Calculate key statistics
    mean_return = annual_returns.mean()
    best_year = annual_returns.idxmax()
    best_value = annual_returns.max()
    worst_year = annual_returns.idxmin()
    worst_value = annual_returns.min()
    negative_years = annual_returns[annual_returns < 0].count()
    total_years = len(annual_returns)

    # Build interpretation message
    message = (
        f"Le portefeuille a enregistré "
        f"une performance moyenne de {mean_return:.2f} % par an. "
        f"La meilleure année a été {best_year} avec un rendement de {best_value:.2f} %, "
        f"tandis que la pire a été {worst_year} avec {worst_value:.2f} %. "
    )

    # Analyze stability based on negative years
    if negative_years == 0:
        message += "Toutes les années ont été positives, ce qui témoigne d'une excellente stabilité."
    elif negative_years == total_years:
        message += "Toutes les années ont été négatives, ce qui suggère une forte sous-performance."
    else:
        message += (
            f"On a enregistré {negative_years} année(s) avec un rendement négatif, "
            "ce qui est normal dans une stratégie long terme mais peut nécessiter une analyse des risques."
        )

    return message

