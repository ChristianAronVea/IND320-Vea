from datetime import date
from pathlib import Path

import streamlit as st

from ind320_vea.help_functions import load_data


pages_folder = Path(__file__).parent / "pages"

pages = [
    st.Page(pages_folder / "1_Home.py", title="Home"),
    st.Page(pages_folder / "2_Reservoir_data_first_month.py", title="Reservoir data first month"),
    st.Page(pages_folder / "3_Reservoir_data.py", title="Reservoir data"),
    st.Page(pages_folder / "6_Reservoir_analysis.py", title="Reservoir analysis"),
    st.Page(pages_folder / "7_Weather_data.py", title="Weather data"),
    st.Page(pages_folder / "8_Weather_analysis.py", title="Weather analysis"),
    st.Page(pages_folder / "4_ENTSOE.py", title="ENTSOE"),
    st.Page(pages_folder / "5_About.py", title="About"),
]

page = st.navigation(pages)
st.session_state.setdefault(
    "weather_date_range",
    (date(2024, 1, 1), date(2024, 12, 31)),
)

# Function to visualize area names
def vis_omraade(omraade):
    omraade_type, nummer = omraade

    if omraade_type == "EL":
        return f"EL{nummer} / NO{nummer}"

    if omraade_type == "NO":
        return "NORWAY"

    if omraade_type == "VASS":
        vaeromraader = {
            1: "RS + RØ",
            2: "RV",
            3: "RM + RN",
        }
        return f"VASS {nummer} / {vaeromraader[nummer]}"

    return f"{omraade_type} {nummer}"


# Visualize the area selection in the sidebar
area_data = load_data()
area_options = sorted({
    (str(area_type), int(area_number))
    for area_type, area_number in area_data[
        ["area_type", "area_number"]
    ].itertuples(index=False, name=None)
})
st.sidebar.selectbox(
    "Area for reservoir and weather data",
    area_options,
    format_func=vis_omraade,
    key="selected_area",
)
st.sidebar.caption(
    "VASS areas use the matching precipitation regions. NO 0 uses all five."
)

page.run()