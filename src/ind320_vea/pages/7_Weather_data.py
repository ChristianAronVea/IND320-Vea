from datetime import date
import streamlit as st

from ind320_vea.weather_functions import (
    download_weather_data,
    validate_weather_dates,
    weather_data_session_key,
    weather_regions_for_area,
)


st.title("Weather data")

# Select date range for weather data. Areas are defined from the sidebar on left.
selected_area = st.session_state["selected_area"]
area_type, area_number = selected_area
selected_dates = st.date_input(
    "Select weather data period",
    value=st.session_state["weather_date_range"],
    min_value=date(1940, 1, 1),
    max_value=date.today(),
)

# Validate that both start and end dates are selected
if len(selected_dates) != 2 or None in selected_dates:
    st.info("Select both a start date and an end date.")
    st.stop()

# Update the session state with the selected date range
start_date, end_date = selected_dates
st.session_state["weather_date_range"] = (start_date, end_date)

# Set regions for the selected area
regions = weather_regions_for_area(selected_area)
region_text = " + ".join(regions)

st.write(f"Selected reservoir area: **{area_type} - area {area_number}**")
st.write(f"Weather regions: **{region_text}**")
st.caption(
    "Weather values are hourly ERA5 averages from 1000 sampled locations "
    "in each selected region. Choose no more than one year at a time."
)

# Validate the selected date range and load the weather data if available in the session
try:
    start_date, end_date = validate_weather_dates(start_date, end_date)
except ValueError as error:
    weather_data = None
    valid_range = False
    st.warning(str(error))
else:
    valid_range = True
    data_key = weather_data_session_key(selected_area, start_date, end_date)
    weather_data = (
        st.session_state.get("weather_data")
        if st.session_state.get("weather_data_key") == data_key
        else None
    )

# Display weather data information.
if weather_data is None and valid_range:
    st.info("Weather data for this area and period has not been loaded.")

    if st.button("Load weather data", type="primary"):
        progress = st.progress(0, text="Preparing the download...")

        def update_progress(current_batch, total_batches):
            progress.progress(
                current_batch / total_batches,
                text=f"Downloading batch {current_batch} of {total_batches}",
            )

        weather_data = download_weather_data(
            selected_area,
            start_date=start_date,
            end_date=end_date,
            progress_callback=update_progress,
        )
        st.session_state["weather_data"] = weather_data
        st.session_state["weather_data_key"] = data_key
        progress.empty()

if weather_data is not None:
    st.success("Weather data for the selected period is ready.")
    st.write(
        f"{len(weather_data):,} hourly records, "
        f"from {weather_data['time'].min()} to {weather_data['time'].max()}."
    )
    st.dataframe(weather_data.head(10), hide_index=True)
