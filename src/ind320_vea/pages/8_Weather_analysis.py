import streamlit as st

from ind320_vea.analysis_functions import (
    plot_precipitation_outliers,
    plot_temperature_lof,
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

st.caption(
    f"Weather data for {selected_area[0]} - area {selected_area[1]}, "
    f"{start_date} to {end_date}"
)

precipitation_tab, temperature_tab = st.tabs(
    ["Outlier / SPC", "Anomaly / LOF"]
)

with precipitation_tab:
    st.subheader("Precipitation outliers")
    if weather_data is None:
        st.info("Load the weather data on the Weather data page first.")
    else:
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

        fig, outliers = plot_precipitation_outliers(
            weather_data,
            cutoff_period_days=cutoff_period_days,
            n_std=n_std,
            display_daily=display_daily,
        )
        st.plotly_chart(fig, width="stretch")
        st.metric("Precipitation outliers", len(outliers))
        st.dataframe(outliers, hide_index=True)

with temperature_tab:
    st.subheader("Temperature anomalies")
    if weather_data is None:
        st.info("Load the weather data on the Weather data page first.")
    else:
        proportion_outliers = st.slider(
            "Proportion of outliers",
            min_value=0.001,
            max_value=0.10,
            value=0.01,
            step=0.001,
        )
        
        st.caption(f"Selected proportion: {proportion_outliers:.1%}")

        fig, anomalies = plot_temperature_lof(
            weather_data,
            proportion_outliers=proportion_outliers,
        )
        st.plotly_chart(fig, width="stretch")
        st.metric("Temperature anomalies", len(anomalies))
        st.dataframe(anomalies, hide_index=True)
