# Flask App 

Une application web simple pour optimizer un portefeuille d'ETF.

## Technologies

- Python 3
- Flask

## Bibliothèques à intaller

pip install flask
pip install yfinance
pip install pandas
pip install numpy
pip install plotly
pip install scikit-learn


## Installation

```bash
git clone https://github.com/GabyRkt/Invest
cd invest
flask --app app run
```


## Fonctionnalités

Saisir des paramètres 
- Montant initial d’investissement 
- Montant des contributions récurrentes (mensuelles, trimestrielles, annuelles) 
- Fréquence des contributions (mensuelle, trimestrielle, semestrielle, annuelle) 
- Durée d’investissement (en années) 
- Frais de gestion annuels (exprimés en pourcentage) 
- Choix des actifs (actions, obligations, ETF) à partir d’une liste d'actifs financiers