import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from ind320_vea.help_functions import load_crossborder_data


st.title("ENTSOE Data")

df = load_crossborder_data()


col1, col2 = st.columns(2)

# Pie Chart - Total MWh for the selected connection
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


# Line Plot - MWh over time for the selected connection
with col2:
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    with st.expander("Choose months", expanded=True):
        selected_months = st.pills(
            "Months",
            months,
            selection_mode="multi",
            width="stretch",
        )

    # Calculat months numbers from the selected months
    if selected_months:
        selected_month_numbers = [
            months.index(month) + 1
            for month in selected_months
        ]
    else:
        selected_month_numbers = []
        st.info("Choose at least one month.")

    # Define plot data
    plot_data = connection_df[
        connection_df["month"].isin(selected_month_numbers)
    ].sort_values("ts")

    if not plot_data.empty:
        fig, ax = plt.subplots()
        for direction in ["in", "out"]:
            direction_data = plot_data[
                plot_data["direction"] == direction
            ]
            ax.plot(
                direction_data["ts"],
                direction_data["mwh"],
                label=f"{direction} to/from Norway",
            )
        ax.set_xlabel("Date")
        ax.set_ylabel("MWh")
        ax.set_title("MWh over Time - One Connection")
        ax.legend()
        fig.autofmt_xdate()
        st.pyplot(fig)





with st.expander("Data source"):
    st.write(
        """
        The data shown on this page comes from ENTSO-E cross-border
        electricity flow data. The data has been aggregated by hour and
        stored in the MongoDB.

        The data contains:
        - electricity flow connections
        - direction (in/out)
        - timestamp
        - year
        - month
        - energy in MWh. 
        
        The direction `in` represents electricity flowing into Norway, while `out` represents electricity flowing out of Norway.
        """
    )