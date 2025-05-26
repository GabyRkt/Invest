import pandas as pd
import numpy as np
import yfinance as yf
from portfolio import Portfolio
from utils import get_etf_info

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
        Simulate passive ETF investing, with fees.
        '''

        # Initial allocation for each ETF in assets based on percentage
        initial_allocations = self.portfolio.initial_amount * self.weights

        first_prices = self.data.loc[self.dates[0]]

        # For the initial investment
        for i, etf in enumerate(self.portfolio.assets):
            price = first_prices[etf.ticker]

            # Get the number of whole units and calculate it's price
            units = np.floor(initial_allocations[i] / price)
            amount_used = units * price

            leftover = initial_allocations[i] - amount_used
            etf.units += units

            # Add the leftover to cash_reserve to use it for the next month
            self.portfolio.cash_reserve += leftover
        
        portfolio_values = []


        # Iterate for each month
        for i, date in enumerate(self.dates):
            
            # ETF price for this month
            prices = self.data.loc[date]
            
            # Based on frequency and skip the first month
            if i % self.months_between_contributions == 0 and i > 0:
                self.portfolio.cash_reserve += self.portfolio.recurring_contribution
                
                for etf in self.portfolio.assets:
                    part = etf.weight * self.portfolio.cash_reserve
                    price = prices[etf.ticker]
                    units_to_buy = np.floor(part / price)
                    amount_used = units_to_buy * price
                    etf.units += units_to_buy
                    self.portfolio.cash_reserve -= amount_used


            # Total portfolio value
            portfolio_value = sum(etf.units * prices[etf.ticker] for etf in self.portfolio.assets)
            portfolio_value += self.portfolio.cash_reserve

            # Apply service fee only after the first month
            if i > 0:
                # Service fee annualy to monthly
                portfolio_value *= (1 - self.portfolio.service_fee / 100 / 12)
            
            portfolio_values.append(portfolio_value)

        result_df = pd.DataFrame({
            "Date": self.dates,
            "Portfolio Value": portfolio_values
        }).set_index("Date")

        return result_df


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

