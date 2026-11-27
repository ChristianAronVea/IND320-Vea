import pandas as pd
import streamlit as st

from ind320_vea.analysis_functions import (
    forecast_reservoir_fill_rate,
    plot_reservoir_forecast_animation,
    weekly_weather_features,
)
from ind320_vea.help_functions import load_data
from ind320_vea.weather_functions import weather_data_session_key


st.title("Reservoir forecasting")

selected_area = st.session_state["selected_area"]
reservoir_data = load_data()
area_data = reservoir_data.loc[
    (reservoir_data["area_type"] == selected_area[0])
    & (reservoir_data["area_number"] == selected_area[1])
]
latest_date = area_data["date_Id"].max().date()
cutoff_date = st.session_state.get("map_selected_date", latest_date)

# Use the map's selected date as the end of the training period.
fill_rate = (
    area_data.loc[area_data["date_Id"] <= pd.Timestamp(cutoff_date)]
    .set_index("date_Id")["fill_rate"]
    .sort_index()
)
fill_rate = pd.to_numeric(fill_rate, errors="raise").dropna()
if len(fill_rate) < 52:
    st.error("At least 52 weekly observations are required for forecasting.")
    st.stop()

st.caption(
    f"{selected_area[0]} {selected_area[1]} - Training data through "
    f"{fill_rate.index[-1].date()}"
)

weather_data = None
weather_range = st.session_state.get("weather_date_range")
if weather_range and len(weather_range) == 2:
    expected_weather_key = weather_data_session_key(
        selected_area, weather_range[0], weather_range[1]
    )
    if st.session_state.get("weather_data_key") == expected_weather_key:
        weather_data = st.session_state.get("weather_data")

weekly_weather = None
weather_options = []
if weather_data is not None:
    weekly_weather = weekly_weather_features(
        weather_data, ["temperature_2m", "precipitation"]
    )
    weather_history_dates = pd.date_range(
        end=fill_rate.index[-1], periods=52, freq="7D"
    )
    if weekly_weather.reindex(weather_history_dates).notna().all().all():
        weather_options = ["temperature_2m", "precipitation"]

if not weather_options:
    st.caption(
        "To use weather inputs, load a complete year of weather data ending "
        "at the selected map date."
    )

with st.form("reservoir_forecast_settings"):
    horizon = st.slider("Forecast horizon (weeks)", 1, 52, 12)
    history = st.slider(
        "Training history (weeks)",
        min_value=52,
        max_value=len(fill_rate),
        value=min(120, len(fill_rate)),
    )

    with st.expander("SARIMAX parameters"):
        first_row = st.columns(4)
        p = first_row[0].number_input("p", min_value=0, max_value=5, value=3)
        d = first_row[1].number_input("d", min_value=0, max_value=5, value=0)
        q = first_row[2].number_input("q", min_value=0, max_value=5, value=3)
        m = first_row[3].selectbox("Season length (m)", [26, 52, 104], index=1)

        second_row = st.columns(3)
        sp = second_row[0].number_input("Seasonal p", 0, 5, 3)
        sd = second_row[1].number_input("Seasonal d", 0, 5, 1)
        sq = second_row[2].number_input("Seasonal q", 0, 5, 1)

    selected_exogenous = st.multiselect(
        "Exogenous weather variables",
        options=weather_options,
        format_func={
            "temperature_2m": "Temperature",
            "precipitation": "Precipitation",
        }.get,
    )
    if selected_exogenous:
        st.caption(
            "Future weather inputs repeat the values from 52 weeks earlier."
        )

    run_forecast = st.form_submit_button("Run forecast", type="primary")

if run_forecast:
    minimum_history = d + m * sd + 1
    if history < minimum_history:
        st.error(
            f"Choose at least {minimum_history} training weeks for these "
            "differencing settings."
        )
        st.stop()

    training_exogenous = None
    future_exogenous = None
    if selected_exogenous:
        training_exogenous = weekly_weather[selected_exogenous]
        future_dates = pd.date_range(
            start=fill_rate.index[-1] + pd.Timedelta(weeks=1),
            periods=horizon,
            freq="7D",
        )
        # Future weather is estimated from the same weeks in the previous year.
        source_dates = future_dates - pd.Timedelta(weeks=52)
        future_exogenous = weekly_weather[selected_exogenous].reindex(source_dates)
        future_exogenous.index = future_dates

    forecast = forecast_reservoir_fill_rate(
        fill_rate,
        horizon=horizon,
        history=history,
        p=p,
        d=d,
        q=q,
        m=m,
        sp=sp,
        sd=sd,
        sq=sq,
        exogenous=training_exogenous,
        future_exogenous=future_exogenous,
    )
    st.plotly_chart(
        plot_reservoir_forecast_animation(
            fill_rate.tail(history), forecast
        ),
        width="stretch",
    )