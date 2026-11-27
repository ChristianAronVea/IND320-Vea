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


def plot_sliding_window_correlation(
    fill_rate,
    weather_data,
    weather_property="temperature_2m",
    lag_weeks=0,
    window_weeks=13,
):
    property_labels = {
        "temperature_2m": "Temperature",
        "precipitation": "Precipitation",
    }
    if weather_property not in property_labels:
        raise ValueError(f"Unsupported weather property: {weather_property}")
    if lag_weeks < 0:
        raise ValueError("Lag must be zero or a positive number of weeks.")
    if window_weeks < 2:
        raise ValueError("Window length must be at least two weeks.")

    hourly_weather = get_hourly_series(weather_data, weather_property)
    # Keep UTC calendar weeks while matching NVE's timezone-naive date labels.
    hourly_weather.index = hourly_weather.index.tz_localize(None)
    weekly_weather = hourly_weather.resample("W-SUN")

    # Match the weekly NVE data and exclude partial weather weeks.
    if weather_property == "precipitation":
        weekly_weather = weekly_weather.sum()
    else:
        weekly_weather = weekly_weather.mean()
    complete_weeks = hourly_weather.resample("W-SUN").count() == 168
    weekly_weather = weekly_weather.where(complete_weeks)

    fill_index = pd.DatetimeIndex(pd.to_datetime(fill_rate.index))
    if fill_index.tz is not None:
        fill_index = fill_index.tz_convert("UTC").tz_localize(None)
    fill_index = fill_index.normalize()
    weekly_fill_rate = pd.Series(
        pd.to_numeric(fill_rate, errors="raise").to_numpy(dtype=float),
        index=fill_index,
    )
    weekly_fill_rate = weekly_fill_rate.groupby(level=0).mean().sort_index()

    valid_fill_dates = weekly_fill_rate.dropna().index
    valid_weather_dates = weekly_weather.dropna().index
    correlation = pd.Series(dtype=float)
    if len(valid_fill_dates) and len(valid_weather_dates):
        # Keep calendar weeks so the lag always means actual weeks, even across gaps.
        week_index = pd.date_range(
            min(valid_fill_dates.min(), valid_weather_dates.min()),
            max(valid_fill_dates.max(), valid_weather_dates.max()),
            freq="W-SUN",
        )
        aligned = pd.DataFrame(
            {
                "fill_rate": weekly_fill_rate.reindex(week_index),
                "weather": weekly_weather.reindex(week_index),
            }
        )

        # A positive lag pairs earlier weather with a later filling observation.
        lagged_weather = aligned["weather"].shift(lag_weeks)
        # Center the window so each correlation is dated at its midpoint.
        correlation = (
            aligned["fill_rate"]
            .rolling(
                window=window_weeks,
                min_periods=window_weeks,
                center=True,
            )
            .corr(lagged_weather)
            .dropna()
        )

    fig = go.Figure()
    if not correlation.empty:
        fig.add_trace(go.Scatter(
            x=correlation.index,
            y=correlation,
            mode="lines",
            line={"color": colors[0]},
            name="Rolling correlation",
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=(
            f"Centered {window_weeks}-week rolling correlation: "
            f"{property_labels[weather_property].lower()} and reservoir filling"
        ),
        xaxis_title="Center week of the rolling window",
        yaxis_title="Pearson correlation",
        yaxis_range=[-1, 1],
        template="plotly_white",
        hovermode="x unified",
    )
    return fig, correlation


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
