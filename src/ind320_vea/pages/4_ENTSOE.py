import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from ind320_vea.help_functions import load_crossborder_data


st.title("ENTSOE Data")

df = load_crossborder_data()


col1, col2 = st.columns(2)

with col1:
    # YEAR - RADIO BUTTONS
    years = sorted(df["year"].unique())
    selected_year = st.radio(
        "Choose year",
        years,
        horizontal=True,
    )

    selected_df = df[df["year"] == selected_year]
    
    
    
    # CONNECTIONS - SELECT BOX
    connections = sorted(selected_df["connection"].unique())
    selected_connection = st.selectbox("Choose connection", connections)
    connection_df = selected_df[
        selected_df["connection"] == selected_connection
    ]
    df_in = connection_df[connection_df["direction"] == "in"]
    df_out = connection_df[connection_df["direction"] == "out"]

    values = [df_in["mwh"].sum(), df_out["mwh"].sum()]      # sum of MWh for in and out directions
    fig, ax = plt.subplots()
    wedges, _, _ = ax.pie(
        values,
        labels=[f"{value:,.0f} MWh" for value in values],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("Total MWh - one connection")
    ax.legend(
        wedges,
        ["In to Norway", "Out from Norway"],
        bbox_to_anchor=(1.2, 1),
    )
    fig.tight_layout()
    st.pyplot(fig)