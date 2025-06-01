import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

def regression(dates, values, scale='linear'):
    """
    Linear regression 
    """
    base_date = dates[0]
    X = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
    y_raw = np.array(values)
    
    # Basic validations
    if len(dates) < 3:
        raise ValueError("At least 3 data points are required")
    
    if np.any(np.isnan(y_raw)) or np.any(np.isinf(y_raw)):
        raise ValueError("Data contains NaN or Inf values")
    
    if scale == 'log' and np.any(y_raw <= 0):
        raise ValueError("Values must be positive for log scale")

    # Data transformation based on scale
    if scale == 'log':
        y = np.log(y_raw)
    else:
        y = y_raw.copy()

    # Linear regression
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    # Calculate residuals
    residuals = y - y_pred
    std_residuals = np.std(residuals)
    
    if scale == 'log':
        # In log scale, std_residuals is already in relative units
        std_residuals_percent = std_residuals * 100  
    else:
        # In linear scale, normalize by mean value and convert to percentage
        mean_value = np.mean(y_raw)
        if mean_value > 0:
            std_residuals_percent = (std_residuals / mean_value) * 100
        else:
            std_residuals_percent = 0
    
    # Extract slope and intercept
    slope = float(model.coef_[0])
    intercept = float(model.intercept_)
    
    # Calculate R²
    r2 = model.score(X, y)
    

    if scale == 'log':
        # In log scale, slope represents daily growth rate
        trend_slope_daily = slope
    else:
        # In linear scale, normalize slope relative to mean value
        mean_value = np.mean(y_raw)
        if mean_value > 0:
            trend_slope_daily = slope / mean_value  # Relative change per day
        else:
            trend_slope_daily = 0
    
    # Calculate difference between actual and predicted values
    last_real = float(y_raw[-1])
    
    # Convert prediction to original space if needed
    if scale == 'log':
        last_pred_original = float(np.exp(y_pred[-1]))
    else:
        last_pred_original = float(y_pred[-1])
    
    # Calculate percentage difference
    if abs(last_real) > 1e-6:
        diff_percent = ((last_real - last_pred_original) / last_real) * 100
    else:
        diff_percent = 0
    
    # Difference in standard deviations
    if std_residuals > 1e-6:
        diff_std = residuals[-1] / std_residuals  # Use raw value for this calculation
        # Limit extreme values
        diff_std = max(min(diff_std, 10), -10)
    else:
        diff_std = 0
    
    return {
        "predicted": y_pred,
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "trend_slope_daily": trend_slope_daily,
        "residual_std": std_residuals_percent,  # Normalized value in percentage
        "residual_std_raw": std_residuals,      # Raw value for calculations
        "diff_percent": diff_percent,
        "diff_std": diff_std
    }


def plot_regression(df, scale='linear', future_months=12):
    """
    Generate regression plot with projections
    """
    dates = df.index.to_list()
    values = df["Portfolio Value"].values
    base_date = dates[0]

    # Convert dates to days
    X = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
    X_future = np.array([(d - base_date).days for d in pd.date_range(dates[0], dates[-1] + pd.DateOffset(months=future_months), freq='MS')]).reshape(-1, 1)

    # Regression model
    model = LinearRegression()
    if scale == 'log':
        y = np.log(values)
    else:
        y = values
    
    model.fit(X, y)
    y_pred_future = model.predict(X_future)
    y_pred_current = model.predict(X)

    # Convert predictions back to original space if necessary
    if scale == 'log':
        y_pred_future = np.exp(y_pred_future)
        y_real = values
    else:
        y_real = values

    residuals = y - y_pred_current
    sigma = np.std(residuals)

    # Confidence bands
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

    fig = go.Figure()

    # Portfolio 
    fig.add_trace(go.Scatter(
        x=dates,
        y=y_real,
        mode='lines',
        name='Portfolio',
        line=dict(color='blue'),
        hovertemplate="%{y:,.0f} €"
    ))

    # Regression line
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=y_pred_future.flatten(),
        mode='lines',
        name='Regression',
        line=dict(color='red'),
        hovertemplate="%{y:,.0f} €"
    ))

    # ±1σ confidence bands
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

    # ±2σ confidence bands
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
        yaxis_title="Value (€)",
        yaxis_type=scale,
        xaxis_tickformat="%b %Y",
        hovermode="x unified"
    )

    return fig.to_html(full_html=False)