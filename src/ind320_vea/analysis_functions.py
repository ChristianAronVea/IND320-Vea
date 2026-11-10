import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

# get the hourly series of a variable from the weather data
def get_hourly_series(weather_data, variable):
    data = weather_data[["time", variable]].copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data[variable] = pd.to_numeric(data[variable], errors="raise")
    series = data.groupby("time")[variable].mean().sort_index()
    
    return series.astype(float)

# High-pass filter using Discrete Cosine Transform (DCT)
def high_pass_dct(values, cutoff_period_days=30):
    coefficients = dct(values, type=2, norm="ortho")
    low_frequency_count = int(np.ceil(2 * len(values) / (cutoff_period_days * 24)))
    coefficients[:max(1, low_frequency_count)] = 0
    return idct(coefficients, type=2, norm="ortho")

# Plot precipitation outliers using DCT-based high-pass filtering and SPC limits
def plot_precipitation_outliers(weather_data, cutoff_period_days=30, n_std=3, display_daily=True):
    precipitation = get_hourly_series(weather_data, "precipitation")
    satv = high_pass_dct(precipitation.to_numpy(), cutoff_period_days)
    center = np.median(satv)
    spread = 1.4826 * np.median(np.abs(satv - center))
    if spread == 0:
        spread = np.std(satv)

    baseline = precipitation.to_numpy() - satv
    lower_limit = baseline + center - n_std * spread
    upper_limit = baseline + center + n_std * spread
    is_outlier = (satv < center - n_std * spread) | (satv > center + n_std * spread)

    if display_daily:
        plot_precipitation = precipitation.resample("D").mean()
        plot_lower_limit = pd.Series(
            lower_limit, index=precipitation.index
        ).resample("D").mean()
        plot_upper_limit = pd.Series(
            upper_limit, index=precipitation.index
        ).resample("D").mean()
        line_label = "Daily average precipitation"
    else:
        plot_precipitation = precipitation
        plot_lower_limit = pd.Series(lower_limit, index=precipitation.index)
        plot_upper_limit = pd.Series(upper_limit, index=precipitation.index)
        line_label = "Hourly average precipitation"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_precipitation.index,
        y=plot_precipitation,
        mode="lines",
        name=line_label,
    ))
    fig.add_trace(go.Scatter(
        x=plot_lower_limit.index,
        y=plot_lower_limit,
        mode="lines",
        line={"color": "darkorange"},
        name="SPC lower limit",
    ))
    fig.add_trace(go.Scatter(
        x=plot_upper_limit.index,
        y=plot_upper_limit,
        mode="lines",
        line={"color": "darkorange"},
        name="SPC upper limit",
    ))
    fig.add_trace(go.Scatter(
        x=precipitation.index[is_outlier],
        y=precipitation.to_numpy()[is_outlier],
        mode="markers",
        marker={"color": "crimson"},
        name="Outlier",
    ))
    fig.update_layout(
        title="Average precipitation with SPC outliers",
        xaxis_title="Time (UTC)",
        yaxis_title="Precipitation (mm/hour)",
        template="plotly_white",
        hovermode="x unified",
    )

    outliers = pd.DataFrame({
        "time": precipitation.index[is_outlier],
        "precipitation": precipitation.to_numpy()[is_outlier],
        "lower_limit": lower_limit[is_outlier],
        "upper_limit": upper_limit[is_outlier],
    })
    return fig, outliers

# Plot temperature anomalies using Local Outlier Factor (LOF)
def plot_temperature_lof(weather_data, proportion_outliers=0.01):
    temperature = get_hourly_series(weather_data, "temperature_2m")
    lof = LocalOutlierFactor(
        n_neighbors=min(20, len(temperature) - 1),
        contamination=proportion_outliers,
    )
    is_anomaly = lof.fit_predict(temperature.to_numpy().reshape(-1, 1)) == -1
    lof_score = -lof.negative_outlier_factor_

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=temperature.index,
        y=temperature,
        mode="lines",
        name="Average temperature",
    ))
    fig.add_trace(go.Scatter(
        x=temperature.index[is_anomaly],
        y=temperature.to_numpy()[is_anomaly],
        mode="markers",
        marker={"color": "crimson"},
        name="LOF anomaly",
    ))
    fig.update_layout(
        title="Average temperature with LOF anomalies",
        xaxis_title="Time (UTC)",
        yaxis_title="Temperature (deg C)",
        template="plotly_white",
        hovermode="x unified",
    )

    outliers = pd.DataFrame({
        "time": temperature.index[is_anomaly],
        "temperature_2m": temperature.to_numpy()[is_anomaly],
        "lof_score": lof_score[is_anomaly],
    })
    return fig, outliers

# STL decomposition of reservoir fill rate
def plot_stl_decomposition(fill_rate, seasonal=13, trend=53, robust=True):
    series = fill_rate.dropna().astype(float).sort_index()

    result = STL(
        series,
        period=52,
        seasonal=seasonal,
        trend=trend,
        robust=robust,
    ).fit()
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
        vertical_spacing=0.08,
    )
    components = (
        result.observed,
        result.trend,
        result.seasonal,
        result.resid,
    )
    for row, component in enumerate(components, start=1):
        fig.add_trace(
            go.Scatter(x=series.index, y=component, mode="lines", showlegend=False),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="Fill rate", row=row, col=1)
    fig.update_layout(
        title="Reservoir filling: STL decomposition",
        template="plotly_white",
        height=800,
    )
    return fig


# Spectrogram of reservoir fill rate
def plot_fill_rate_spectrogram(fill_rate, window_length=52, window_overlap=26):
    series = fill_rate.dropna().astype(float).sort_index()

    frequencies, times, power = spectrogram(
        series.to_numpy(),
        fs=1.0,
        window="hann",
        nperseg=window_length,
        noverlap=window_overlap,
        scaling="density",
        mode="psd",
    )
    dates = series.index[0] + pd.to_timedelta(times * 7, unit="D")
    power_db = 10 * np.log10(np.maximum(power[1:], np.finfo(float).tiny))

    fig = go.Figure(
        data=go.Heatmap(
            x=dates,
            y=frequencies[1:],
            z=power_db,
            colorscale="Viridis",
            colorbar={"title": "Power (dB)"},
        )
    )
    fig.update_layout(
        title="Reservoir filling: spectrogram",
        xaxis_title="Time",
        yaxis_title="Frequency (cycles per week)",
        yaxis_type="log",
        template="plotly_white",
    )
    return fig
