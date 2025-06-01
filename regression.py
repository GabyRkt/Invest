import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

def regression(dates, values, scale='linear'):
    base_date = dates[0]
    X = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
    y_raw = np.array(values).reshape(-1, 1)
    
    # Vérifications
    if np.any(np.isnan(y_raw)) or np.any(np.isinf(y_raw)):
        raise ValueError("Les données contiennent des NaN ou Inf")
    
    if scale == 'log' and np.any(y_raw <= 0):
        raise ValueError("Les valeurs doivent être positives pour l'échelle log")

    # Application du log si demandé
    if scale == 'log':
        y = np.log(y_raw)
    else:
        y = y_raw

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    residuals = y - y_pred
    std_residuals = np.std(residuals)
    slope = model.coef_[0][0]

    # ✅ Calcul correct de la croissance annualisée
    if scale == 'log':
        annual_growth = (np.exp(slope * 365.25) - 1) * 100
    else:
        # Pour l'échelle linéaire, utiliser la pente directement
        start_value = y_raw[0][0]
        if start_value != 0:
            annual_growth = (slope * 365.25 / start_value) * 100
        else:
            annual_growth = np.nan

    # Comparaison cohérente dans le même espace
    if scale == 'log':
        last_real = np.log(y_raw[-1][0])
        last_pred = y_pred[-1][0]
    else:
        last_real = y_raw[-1][0]
        last_pred = y_pred[-1][0]

    pct_diff = ((np.exp(last_real) - np.exp(last_pred)) / np.exp(last_pred) * 100) if scale == 'log' else ((last_real - last_pred) / last_pred * 100)
    std_diff = (last_real - last_pred) / std_residuals

    return {
        "predicted": y_pred.flatten(),
        "slope": slope,
        "intercept": model.intercept_[0],
        "r2": model.score(X, y),
        "growth_annualized": annual_growth,
        "residual_std": std_residuals,
        "diff_percent": pct_diff,
        "diff_std": std_diff
    }




def plot_regression(df, reg_result, scale='linear', future_months=12):
    dates = df.index.to_list()
    values = df["Portfolio Value"].values
    base_date = dates[0]

    # Convertir les dates en jours
    X = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
    X_future = np.array([(d - base_date).days for d in pd.date_range(dates[0], dates[-1] + pd.DateOffset(months=future_months), freq='MS')]).reshape(-1, 1)

    # Modèle de régression
    model = LinearRegression()
    y = np.log(values) if scale == 'log' else values
    model.fit(X, y)
    y_pred = model.predict(X_future)

    if scale == 'log':
        y_pred = np.exp(y_pred)
        y_real = values
    else:
        y_real = values

    # Résidus et bandes de confiance
    residuals = y - model.predict(X)
    sigma = np.std(residuals)

    if scale == 'log':
        upper_1 = np.exp(model.predict(X_future) + sigma)
        lower_1 = np.exp(model.predict(X_future) - sigma)
        upper_2 = np.exp(model.predict(X_future) + 2 * sigma)
        lower_2 = np.exp(model.predict(X_future) - 2 * sigma)
    else:
        upper_1 = model.predict(X_future) + sigma
        lower_1 = model.predict(X_future) - sigma
        upper_2 = model.predict(X_future) + 2 * sigma
        lower_2 = model.predict(X_future) - 2 * sigma

    future_dates = pd.date_range(dates[0], dates[-1] + pd.DateOffset(months=future_months), freq='MS')

    # Graphique
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=y_real,
        mode='lines',
        name='Portefeuille',
        line=dict(color='blue'),
        hovertemplate="%{y:,.0f} €"
    ))

    fig.add_trace(go.Scatter(
        x=future_dates,
        y=y_pred.flatten(),
        mode='lines',
        name='Régression',
        line=dict(color='red'),
        hovertemplate="%{y:,.0f} €"
    ))

    # Bandes ±1σ
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=upper_1.flatten(),
        mode='lines',
        name='+1σ',
        line=dict(color='gray', dash='dash'),
        showlegend=False,
        hovertemplate="+1σ : %{y:,.0f} €<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=lower_1.flatten(),
        mode='lines',
        name='-1σ',
        line=dict(color='gray', dash='dash'),
        showlegend=False,
        hovertemplate="-1σ : %{y:,.0f} €<extra></extra>"
    ))

    # Bandes ±2σ
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=upper_2.flatten(),
        mode='lines',
        name='+2σ',
        line=dict(color='lightgray', dash='dot'),
        showlegend=False,
        hovertemplate="+2σ : %{y:,.0f} €<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=lower_2.flatten(),
        mode='lines',
        name='-2σ',
        line=dict(color='lightgray', dash='dot'),
        showlegend=False,
        hovertemplate="-2σ : %{y:,.0f} €<extra></extra>"
    ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Valeur (€)",
        yaxis_type=scale,
        xaxis_tickformat="%b %Y",
        hovermode="x unified"
    )

    return fig.to_html(full_html=False)
