import streamlit as st

from ind320_vea.analysis_functions import (
    plot_fill_rate_spectrogram,
    plot_stl_decomposition,
)
from ind320_vea.help_functions import load_data


st.title("Reservoir analysis")

selected_area = st.session_state["selected_area"]
data = load_data()
area_data = data[
    (data["area_type"] == selected_area[0])
    & (data["area_number"] == selected_area[1])
]
fill_rate = area_data.set_index("date_Id")["fill_rate"].sort_index()

st.caption(f"Magasinstatistikk for {selected_area[0]} - area {selected_area[1]}")

stl_tab, spectrogram_tab = st.tabs(["STL", "Spectrogram"])

with stl_tab:
    st.subheader("Seasonal-Trend decomposition using LOESS")
    seasonal = st.slider(
        "Seasonal smoother (weeks)",
        min_value=7,
        max_value=25,
        value=13,
        step=2,
    )
    trend = st.slider(
        "Trend smoother (weeks)",
        min_value=53,
        max_value=105,
        value=53,
        step=2,
    )
    robust = st.checkbox("Robust fitting", value=True)

    st.plotly_chart(
        plot_stl_decomposition(
            fill_rate, seasonal=seasonal, trend=trend, robust=robust
        ),
        width="stretch",
    )

with spectrogram_tab:
    st.subheader("Spectrogram")
    window_length = st.slider(
        "Window length (weeks)",
        min_value=2,
        max_value=min(104, len(fill_rate)),
        value=min(52, len(fill_rate)),
    )
    window_overlap = st.slider(
        "Window overlap (weeks)",
        min_value=0,
        max_value=window_length - 1,
        value=min(26, window_length - 1),
    )

    st.plotly_chart(
        plot_fill_rate_spectrogram(
            fill_rate,
            window_length=window_length,
            window_overlap=window_overlap,
        ),
        width="stretch",
    )
