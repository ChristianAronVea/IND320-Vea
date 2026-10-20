import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
    selected_connection = st.radio("Choose connection", connections)
    connection_df = selected_df[
        selected_df["connection"] == selected_connection
    ]
    df_in = connection_df[connection_df["direction"] == "in"]
    df_out = connection_df[connection_df["direction"] == "out"]

    
    
    # PIE CHART
    direction_colors = ["#1b7390", "#cf771f"]
    values = [df_in["mwh"].sum(), df_out["mwh"].sum()]      # sum of MWh for in and out directions
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["In to Norway", "Out from Norway"],
                values=values,
                marker_colors=direction_colors,
                texttemplate="%{value:,.0f} MWh<br>%{percent}",
                textposition="inside",
                insidetextorientation="horizontal",
                sort=False,
                rotation=90,
            )
        ]
    )
    fig.update_layout(
        title="Total MWh",
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.1,
            yanchor="top",
        ),
        height=520,
        margin=dict(l=0, r=0, t=100, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


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

    # EXPANDER - MONTHS
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


    # LINE PLOT
    if not plot_data.empty:
        line_data = (
            plot_data
            .pivot(index="ts", columns="direction", values="mwh")
            .reindex(columns=["in", "out"])
            .sort_index()
        )
        line_fig = go.Figure()
        direction_labels = {
            "in": "In to Norway",
            "out": "Out from Norway",
        }
        for direction, color in zip(["in", "out"], direction_colors):
            line_fig.add_trace(
                go.Scatter(
                    x=line_data.index,
                    y=line_data[direction],
                    mode="lines",
                    name=direction_labels[direction],
                    line=dict(color=color),
                )
            )
        line_fig.update_layout(
            title=dict(
                text="MWh over time",
                y=0.8,
                yanchor="bottom",
            ),
            xaxis_title="Date",
            yaxis_title="MWh",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.3,
                yanchor="bottom",
            ),
            height=600,
            margin=dict(t=140),
        )
        st.plotly_chart(line_fig, use_container_width=True)



# DATA SOURCE
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