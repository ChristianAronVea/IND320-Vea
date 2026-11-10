import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ind320_vea.help_functions import load_data

st.title("Reservoir Data First Month")

df = load_data("1995-01", "1995-02")  # Load the data for the first month in the dataset

# Use the area selected in the sidebar.
selected_area = st.session_state["selected_area"]
df = df[
    (df["area_type"] == selected_area[0])
    & (df["area_number"] == selected_area[1])
]

# Convert the date column to datetime
df["date_Id"] = pd.to_datetime(df["date_Id"])

# Sort the data chronologically before creating the table
df = df.sort_values("date_Id").reset_index(drop=True)

# Select all observations from the first month
first_month = df["date_Id"].min().strftime("%Y-%m")
first_month_df = df[df["date_Id"].dt.strftime("%Y-%m") == first_month]



st.write("First month:", first_month)

measurement_columns = [
    "fill_rate",
    "capacity_TWh",
    "storage_TWh",
    "fill_rate_previous_week",
    "fill_rate_change",
]
plot_columns = [
    column for column in measurement_columns
    if column in first_month_df and pd.api.types.is_numeric_dtype(first_month_df[column])
]

fig = make_subplots(
    rows=len(plot_columns),
    cols=1,
    shared_xaxes=True,
    subplot_titles=plot_columns,
    vertical_spacing=0.08,
)
for row, column in enumerate(plot_columns, start=1):
    fig.add_trace(
        go.Scatter(
            x=first_month_df["date_Id"],
            y=first_month_df[column],
            mode="lines+markers",
            name=column,
            showlegend=False,
        ),
        row=row,
        col=1,
    )
fig.update_layout(
    title=f"Reservoir measurements for {selected_area[0]} - area {selected_area[1]}",
    template="plotly_white",
    height=max(300, 220 * len(plot_columns)),
)
st.plotly_chart(fig, width="stretch")