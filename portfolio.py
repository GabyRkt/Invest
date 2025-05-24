import pandas as pd

class Asset:
    def __init__(self, ticker, weight):
        self.ticker = ticker
        self.weight = weight  # en pourcentage (ex: 25.0 pour 25%)

class Portfolio:
    def __init__(self, initial_amount, recurring_contrib, frequency, start_date, end_date,fee,assets=None):
        self.initial_amount = initial_amount
        self.recurring_contrib = recurring_contrib
        self.frequency = frequency
        self.start_date = start_date
        self.end_date = end_date
        self.fee = fee        
        self.assets = assets if assets else []  # liste de Asset
        self._validate_assets()
        self.final_amount = self._calculate_final_amount()

    def _calculate_final_amount(self):
        freq_map = {
            'monthly': 'M',
            'quaterly': 'Q',
            'semiannual': 'S',
            'annual': 'A'
        }

        if self.frequency not in freq_map:
            raise ValueError("Fréquence non supportée")

        dates = pd.date_range(self.start_date, self.end_date, freq=freq_map[self.frequency])
        total_contrib = len(dates) * self.recurring_contrib

        return self.initial_amount + total_contrib

    def summary(self):
        return {
            "Montant initial (€)": self.initial_amount,
            "Montant récurrent (€)": self.recurring_contrib,
            "Fréquence": self.frequency,
            "Date de début": self.start_date.strftime("%m/%Y"),
            "Date de fin": self.end_date.strftime("%m/%Y"),
            "Frais de services (%)": self.fee,
            "Montant final estimé (€)": round(self.final_amount, 2),
             "Allocation": {asset.ticker: f"{asset.weight}%" for asset in self.assets}
        }

