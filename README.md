# Flask App avec Base de Données SQLite

Une application web simple en Flask avec une base de données SQLite pour comparer les stratégies d'investissements.

## Fonctionnalités

Saisir des paramètres 
- Montant initial d’investissement 
- Montant des contributions récurrentes (mensuelles, trimestrielles, annuelles) 
- Fréquence des contributions (mensuelle, trimestrielle, semestrielle, annuelle) 
- Durée d’investissement (en années) 
- Frais de gestion annuels (exprimés en pourcentage) 
- Choix des actifs (actions, obligations, ETF) à partir d’une liste d'actifs financiers


## Technologies

- Python 3
- Flask
- SQLite
- SQLAlchemy

## Installation

```bash
git clone https://github.com/GabyRkt/Invest
cd invest
flask --app app run
