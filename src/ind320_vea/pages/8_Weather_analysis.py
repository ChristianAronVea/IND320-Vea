import streamlit as st

from ind320_vea.analysis_functions import (
    plot_weather_outliers,
    plot_weather_lof,
)
from ind320_vea.weather_functions import weather_data_session_key


st.title("Weather analysis")

selected_area = st.session_state["selected_area"]
start_date, end_date = st.session_state["weather_date_range"]
data_key = weather_data_session_key(selected_area, start_date, end_date)
weather_data = (
    st.session_state.get("weather_data")
    if st.session_state.get("weather_data_key") == data_key
    else None
)

st.caption(f"Weather data for interval: {start_date} to {end_date}")

spc_tab, lof_tab = st.tabs(
    ["Outlier / SPC", "Anomaly / LOF"]
)

# SPC/SATV
with spc_tab:
    if weather_data is None:
        st.info("Load the weather data on the Weather data page first.")
    else:
        weather_property = st.radio(
            "Weather property SATV",
            options=["temperature_2m", "precipitation"],
            format_func=lambda value: {
                "temperature_2m": "Temperature",
                "precipitation": "Precipitation",
            }[value],
            horizontal=True,
        )
        property_name = {
            "temperature_2m": "Temperature",
            "precipitation": "Precipitation",
        }[weather_property]
        st.subheader(f"{property_name} outliers")

        cutoff_period_days = st.slider(
            "DCT cutoff period (days)",
            min_value=7,
            max_value=90,
            value=30,
        )
        n_std = st.slider(
            "Robust standard deviations",
            min_value=1.0,
            max_value=5.0,
            value=3.0,
            step=0.5,
        )
        display_daily = st.checkbox("Show daily average", value=True)

        fig, outliers = plot_weather_outliers(
            weather_data,
            cutoff_period_days=cutoff_period_days,
            n_std=n_std,
            display_daily=display_daily,
            weather_property=weather_property,
        )

        st.plotly_chart(fig, width="stretch")
        st.metric(f"{property_name} outliers", len(outliers))
        st.dataframe(outliers, hide_index=True)


# LOF
with lof_tab:
    if weather_data is None:
        st.info("Load the weather data on the Weather data page first.")
    else:
        weather_property_lof = st.radio(
            "LOF weather property",
            options=["temperature_2m", "precipitation"],
            format_func=lambda value: {
                "temperature_2m": "Temperature",
                "precipitation": "Precipitation",
            }[value],
            horizontal=True,
            key="lof_weather_property",
        )
        property_name_lof = {
            "temperature_2m": "Temperature",
            "precipitation": "Precipitation",
        }[weather_property_lof]
        st.subheader(f"{property_name_lof} anomalies")

        proportion_outliers = st.slider(
            "Proportion of outliers",
            min_value=0.001,
            max_value=0.10,
            value=0.01,
            step=0.001,
        )
        
        st.caption(f"Selected proportion: {proportion_outliers:.1%}")

        fig, anomalies = plot_weather_lof(
            weather_data,
            proportion_outliers=proportion_outliers,
            weather_property=weather_property_lof,
        )
        st.plotly_chart(fig, width="stretch")
        st.metric(f"{property_name_lof} anomalies", len(anomalies))
        st.dataframe(anomalies, hide_index=True)
