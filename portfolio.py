import pandas as pd
from etf_search import get_etf_name
import yfinance as yf

class Asset:
    def __init__(self, ticker, weight, fee=0.0):
        self.ticker = ticker
        self.weight = weight / 100 # convert to proportion (ex. 70 to 0.70)
        self.units = 0



class Portfolio:
    def __init__(self, assets, initial_amount, recurring_contribution, contribution_frequency, start_date, end_date, service_fee):
        self.assets = assets  # list of ETF in asset
        self.initial_amount = initial_amount
        self.recurring_contribution = recurring_contribution
        self.contribution_frequency = contribution_frequency 
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.service_fee = service_fee
        self.cash_reserve = 0.0
        self.history = []
        self.final_amount = self._calculate_final_amount()

    def _calculate_final_amount(self):
        freq_map = {
            'Mensuel': 'ME',
            'Trimestriel': 'Q',
            'Semestriel': 'S',
            'Annuel': 'A'
        }

        dates = pd.date_range(self.start_date, self.end_date, freq=freq_map[self.contribution_frequency])
        total_contribution = len(dates) * self.recurring_contribution

        return self.initial_amount + total_contribution



    def print_summary(self):
        allocation = {
        asset.ticker: {
            "name": get_etf_name(asset.ticker),
            "allocation": f"{asset.weight * 100:.1f}%"
        }
        for asset in self.assets
        }

        return {
            "Montant initial (€)": self.initial_amount,
            "Montant récurrent (€)": self.recurring_contribution,
            "Fréquence": self.contribution_frequency,
            "Date de début": self.start_date.strftime("%m/%Y"),
            "Date de fin": self.end_date.strftime("%m/%Y"),
            "Frais de services (%)": self.service_fee,
            "Valeur du portefeuille (€)": round(self.final_amount, 2),
            "Allocation des ETFs": allocation
        }

