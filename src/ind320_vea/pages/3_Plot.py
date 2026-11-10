import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ind320_vea.help_functions import load_data

st.title("Plot")

# first month in the dataset
months = pd.period_range(
    start="1995-01",
    end=pd.Timestamp.today().to_period("M"),
    freq="M",
)


# SLIDER - choose a month range to load and plot
selected_month = st.select_slider(
    "Select month",
    options=months,
    value=(months[0], months[1]),
    format_func=str,
)

start_date = selected_month[0].start_time
end_date = selected_month[1].end_time

df = load_data(start_date, end_date)        # Load the data for the selected month range


selected_area = st.session_state["selected_area"]

# SELECT BOX
# Only numeric measurements can be plotted against the date axis.
numeric_columns = [
    "fill_rate",
    "capacity_TWh",
    "storage_TWh",
    "fill_rate_previous_week",
    "fill_rate_change",
]
columns = ["All numeric columns"] + numeric_columns

# Let the user choose which column to plot
selected_column = st.selectbox(
    "Select data to plot",
    columns
)

st.write("Selected:", selected_column)



# Filter the data to the selected month range
month_data = df[
    (df["area_type"] == selected_area[0])
    & (df["area_number"] == selected_area[1])
]

# Select the data to plot
if selected_column == "All numeric columns":
    plot_columns = numeric_columns
else:
    plot_columns = [selected_column]

plot_data = month_data[["date_Id"] + plot_columns].sort_values("date_Id")

# Create the plot
fig = go.Figure()
for column in plot_columns:
    fig.add_trace(
        go.Scatter(
            x=plot_data["date_Id"],
            y=plot_data[column],
            mode="lines",
            name=column,
        )
    )
fig.update_layout(
    title="Reservoir data over time",
    xaxis_title="Date",
    yaxis_title="Value",
    template="plotly_white",
    hovermode="x unified",
)
st.plotly_chart(fig, width="stretch")