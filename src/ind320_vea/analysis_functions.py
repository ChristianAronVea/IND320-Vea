import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

# color theme on graphs
colors = ["#1b7390", "#cf771f", "#2aaa2a", "#ffff03", "#FF2CDC"]

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

# Plot weather outliers using DCT-based high-pass filtering and SPC limits
def plot_weather_outliers(
    weather_data,
    cutoff_period_days=30,
    n_std=3,
    display_daily=True,
    weather_property="temperature_2m",
):
    property_labels = {
        "temperature_2m": ("Temperature", "deg C"),
        "precipitation": ("Precipitation", "mm/hour"),
    }
    if weather_property not in property_labels:
        raise ValueError(f"Unsupported weather property: {weather_property}")

    property_name, unit = property_labels[weather_property]
    series = get_hourly_series(weather_data, weather_property)
    satv = high_pass_dct(series.to_numpy(), cutoff_period_days)
    center = np.median(satv)
    spread = 1.4826 * np.median(np.abs(satv - center))
    if spread == 0:
        spread = np.std(satv)

    baseline = series.to_numpy() - satv
    lower_limit = baseline + center - n_std * spread
    upper_limit = baseline + center + n_std * spread
    is_outlier = (satv < center - n_std * spread) | (satv > center + n_std * spread)

    if display_daily:
        plot_series = series.resample("D").mean()
        plot_lower_limit = pd.Series(
            lower_limit, index=series.index
        ).resample("D").mean()
        plot_upper_limit = pd.Series(
            upper_limit, index=series.index
        ).resample("D").mean()
        line_label = f"Daily average {property_name.lower()}"
    else:
        plot_series = series
        plot_lower_limit = pd.Series(lower_limit, index=series.index)
        plot_upper_limit = pd.Series(upper_limit, index=series.index)
        line_label = f"Hourly average {property_name.lower()}"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_series.index,
        y=plot_series,
        line={"color": colors[0]},
        mode="lines",
        name=line_label,
    ))
    fig.add_trace(go.Scatter(
        x=plot_lower_limit.index,
        y=plot_lower_limit,
        mode="lines",
        line={"color": colors[1]},
        name="SPC lower limit",
    ))
    fig.add_trace(go.Scatter(
        x=plot_upper_limit.index,
        y=plot_upper_limit,
        mode="lines",
        line={"color": colors[1]},
        name="SPC upper limit",
    ))
    fig.add_trace(go.Scatter(
        x=series.index[is_outlier],
        y=series.to_numpy()[is_outlier],
        mode="markers",
        marker={"color":"crimson"},
        name="Outlier",
    ))
    fig.update_layout(
        title=f"Average {property_name.lower()} with SPC outliers",
        xaxis_title="Time (UTC)",
        yaxis_title=f"{property_name} ({unit})",
        template="plotly_white",
        hovermode="x unified",
    )

    outliers = pd.DataFrame({
        "time": series.index[is_outlier],
        weather_property: series.to_numpy()[is_outlier],
        "lower_limit": lower_limit[is_outlier],
        "upper_limit": upper_limit[is_outlier],
    })
    return fig, outliers

# Plot weather anomalies using Local Outlier Factor (LOF)
def plot_weather_lof(
    weather_data,
    proportion_outliers=0.01,
    weather_property="temperature_2m",
):
    property_labels = {
        "temperature_2m": ("Temperature", "deg C"),
        "precipitation": ("Precipitation", "mm/hour"),
    }
    if weather_property not in property_labels:
        raise ValueError(f"Unsupported weather property: {weather_property}")

    property_name, unit = property_labels[weather_property]
    series = get_hourly_series(weather_data, weather_property)
    lof = LocalOutlierFactor(
        n_neighbors=min(20, len(series) - 1),
        contamination=proportion_outliers,
    )
    is_anomaly = lof.fit_predict(series.to_numpy().reshape(-1, 1)) == -1
    lof_score = -lof.negative_outlier_factor_

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series,
        mode="lines",
        line={"color": colors[0]},
        name=f"Average {property_name.lower()}",
    ))
    fig.add_trace(go.Scatter(
        x=series.index[is_anomaly],
        y=series.to_numpy()[is_anomaly],
        mode="markers",
        marker={"color": "crimson"},
        name="LOF anomaly",
    ))
    fig.update_layout(
        title=f"Average {property_name.lower()} with LOF anomalies",
        xaxis_title="Time (UTC)",
        yaxis_title=f"{property_name} ({unit})",
        template="plotly_white",
        hovermode="x unified",
    )

    outliers = pd.DataFrame({
        "time": series.index[is_anomaly],
        weather_property: series.to_numpy()[is_anomaly],
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
            go.Scatter(x=series.index, y=component, mode="lines", showlegend=False, 
                       line={"color": colors[row - 1]}),
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
            colorscale=[[0, colors[3]], [0.33, colors[2]], [0.67, colors[1]], [1, colors[0]]],
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
