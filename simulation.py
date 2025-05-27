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

        # Initial investment
        for i, etf in enumerate(self.portfolio.assets):
            price = first_prices[etf.ticker]

            # Get the number of whole units that can be bought and calculate it's price
            units = np.floor(initial_allocations[i] / price)
            amount_used = units * price
            etf.units += units

            # Add the leftover to cash_reserve to use it for the next month
            self.portfolio.cash_reserve += initial_allocations[i] - amount_used
        
        portfolio_values = []
        monthly_fee_rate = self.portfolio.service_fee / 100 / 12


        # Simulation loop (based on frenquency) 
        for i, date in enumerate(self.dates):
            current_prices = self.data.loc[date]
            
            # Recurring contributions
            if i % self.months_between_contributions == 0 and i > 0:
                self.portfolio.cash_reserve += self.portfolio.recurring_contribution
                
                # Buy ETF units using the new amount of cash
                for etf in self.portfolio.assets:
                    allocation_amount = etf.weight * self.portfolio.cash_reserve
                    price = current_prices[etf.ticker]
                    units_to_buy = np.floor(allocation_amount / price)
                    amount_used = units_to_buy * price
                    
                    etf.units += units_to_buy
                    self.portfolio.cash_reserve -= amount_used


            # Total portfolio value
            portfolio_value = sum(etf.units * current_prices[etf.ticker] for etf in self.portfolio.assets)
            portfolio_value += self.portfolio.cash_reserve

            # Apply service fee only after the first month
            if i > 0:
                portfolio_value *= (1 - monthly_fee_rate)
            
            portfolio_values.append(portfolio_value)

        # Create a dataframe with the portfolio values
        result_df = pd.DataFrame({
            "Date": self.dates,
            "Portfolio Value": portfolio_values
        }).set_index("Date")

        return result_df

