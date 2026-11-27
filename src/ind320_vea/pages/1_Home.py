import streamlit as st

st.title("IND320 - Christian Aron Vea")
st.write(
    "Explore Norwegian reservoir filling, weather, and cross-border electricity flows."
)

entsoe_column, reservoir_column, weather_column = st.columns(3)

with entsoe_column:
    with st.container(border=True):
        st.subheader("⚡ ENTSO-E")
        st.caption("Cross-border electricity flows")
        st.page_link(
            "pages/4_ENTSOE.py",
            label="Explore electricity flows",
            icon="⚡",
            use_container_width=True,
        )

with reservoir_column:
    with st.container(border=True):
        st.subheader("💧 Reservoir")
        st.caption("Norwegian reservoir data and analysis")
        st.page_link(
            "pages/2_Reservoir_data_first_month.py",
            label="First month",
            icon="🗓️",
            use_container_width=True,
        )
        st.page_link(
            "pages/3_Reservoir_data.py",
            label="Reservoir data",
            icon="📈",
            use_container_width=True,
        )
        st.page_link(
            "pages/6_Reservoir_analysis.py",
            label="Reservoir analysis",
            icon="🔬",
            use_container_width=True,
        )

with weather_column:
    with st.container(border=True):
        st.subheader("🌦️ Weather")
        st.caption("Weather data and analysis")
        st.page_link(
            "pages/7_Weather_data.py",
            label="Weather data",
            icon="🌡️",
            use_container_width=True,
        )
        st.page_link(
            "pages/8_Weather_analysis.py",
            label="Weather analysis",
            icon="🌧️",
            use_container_width=True,
        )